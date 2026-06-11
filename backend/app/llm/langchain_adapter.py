"""LangChain ChatModel adapter — 将自定义 BaseLLMProvider 包装为 LangChain BaseChatModel.

支持 DeepSeek / Kimi / Qwen 三个后端，所有后端都是 OpenAI 兼容 API。
"""

import asyncio
import json
from typing import Any, AsyncIterator, Iterator, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

from app.llm.base import LLMConfig, LLMMessage, LLMTool
from app.llm.registry import get_provider


# ---------------------------------------------------------------------------
# 消息格式转换
# ---------------------------------------------------------------------------

def _langchain_to_custom(messages: list[BaseMessage]) -> list[LLMMessage]:
    """LangChain BaseMessage 列表 → 自定义 LLMMessage 列表"""
    role_map = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "tool",
    }
    result = []
    for m in messages:
        role = role_map.get(m.type, "user")
        content = m.content
        # 处理 content 可能是 list 的情况（如多模态）
        if isinstance(content, list):
            text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
            content = "\n".join(text_parts) or str(content)
        result.append(LLMMessage(role=role, content=str(content)))
    return result


def _langchain_tools_to_custom(tools: list[dict] | None) -> list[LLMTool] | None:
    """LangChain tool 格式 → 自定义 LLMTool"""
    if not tools:
        return None
    result = []
    for t in tools:
        result.append(LLMTool(
            name=t.get("name", ""),
            description=t.get("description", ""),
            parameters=t.get("parameters", {}),
        ))
    return result


# ---------------------------------------------------------------------------
# ChatModel
# ---------------------------------------------------------------------------

class NovelWriterChatModel(BaseChatModel):
    """将 BaseLLMProvider 包装为 LangChain BaseChatModel。

    使用方式:
        model = NovelWriterChatModel(provider_name="deepseek", model_name="deepseek-chat")
        response = model.invoke([HumanMessage(content="你好")])
    """

    provider_name: str = Field(default="deepseek", description="Provider 名称: deepseek/kimi/qwen")
    model_name: str = Field(default="deepseek-chat", description="模型名")
    max_tokens: int = Field(default=16000, description="最大输出 token 数")
    temperature: float = Field(default=0.7, description="采样温度")
    top_p: float = Field(default=0.9, description="nucleus 采样")

    _provider = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return f"novel-writer-{self.provider_name}"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    def _get_provider(self):
        if self._provider is None:
            self._provider = get_provider(self.provider_name)
        return self._provider

    def _convert_tool_calls_to_ai_message(self, content: str) -> AIMessage:
        """尝试从 provider 返回的内容中解析 tool_calls"""
        # 对于 OpenAI 兼容 API，tool calls 在 response 层面处理
        # 这里 provider.generate 已经返回了 content 字符串
        # 如果 content 是 JSON 格式的 tool 调用，包装为 AIMessage
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "tool" in data:
                return AIMessage(
                    content="",
                    tool_calls=[{
                        "id": "call_0",
                        "name": data["tool"],
                        "args": json.loads(data.get("args", "{}")) if isinstance(data.get("args"), str) else data.get("args", {}),
                    }],
                )
        except (json.JSONDecodeError, TypeError):
            pass
        return AIMessage(content=content)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        provider = self._get_provider()
        custom_msgs = _langchain_to_custom(messages)

        # 处理 tools (从 kwargs 或消息中提取)
        tools_schema = None
        if "tools" in kwargs:
            tools_schema = [{
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
            } for t in kwargs["tools"]] if kwargs["tools"] else None

        config = LLMConfig(
            model=kwargs.get("model_override", self.model_name),
            max_tokens=kwargs.get("max_tokens_override", self.max_tokens),
            temperature=kwargs.get("temperature_override", self.temperature),
            top_p=self.top_p,
        )

        # 同步调用（在 async 上下文中用 asyncio.run 可能有问题，所以改用异步路径）
        # BaseChatModel._generate 在 invoke 时会被调用，如果环境是 async 则走 _agenerate
        # 这里用 asyncio.get_event_loop 尝试
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在 async 上下文中，用 nest_asyncio 或直接走同步路径
                import httpx
                # 同步 HTTP 调用
                resp = self._sync_generate(provider, custom_msgs, config, tools_schema)
            else:
                resp = loop.run_until_complete(provider.generate(custom_msgs, config))
        except RuntimeError:
            resp = asyncio.run(provider.generate(custom_msgs, config))

        message = self._convert_tool_calls_to_ai_message(resp.content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation], llm_output={
            "model": resp.model,
            "usage": resp.usage,
        })

    def _sync_generate(self, provider, custom_msgs, config, tools_schema):
        """同步 HTTP 调用版本（用于 async 上下文中）"""
        import httpx
        from app.config import settings

        provider_name = self.provider_name
        api_key = getattr(settings, f"{provider_name.upper()}_API_KEY", "")
        base_url = getattr(settings, f"{provider_name.upper()}_BASE_URL", "").rstrip("/")

        if provider_name == "deepseek":
            api_key = settings.DEEPSEEK_API_KEY
            base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        elif provider_name == "kimi":
            api_key = settings.KIMI_API_KEY
            base_url = settings.KIMI_BASE_URL.rstrip("/")
        elif provider_name == "qwen":
            api_key = settings.QWEN_API_KEY
            base_url = settings.QWEN_BASE_URL.rstrip("/")

        body = {
            "model": config.model or self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in custom_msgs],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }
        if tools_schema:
            body["tools"] = tools_schema

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            content = choice["message"].get("content", "") or ""

            from app.llm.base import LLMResponse
            return LLMResponse(
                content=content,
                model=data["model"],
                usage=data.get("usage", {}),
            )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """同步流式生成。通常使用 _astream。"""
        provider = self._get_provider()
        custom_msgs = _langchain_to_custom(messages)

        config = LLMConfig(
            model=kwargs.get("model_override", self.model_name),
            max_tokens=kwargs.get("max_tokens_override", self.max_tokens),
            temperature=kwargs.get("temperature_override", self.temperature),
            top_p=self.top_p,
        )

        # 同步流式
        import httpx
        from app.config import settings

        provider_name = self.provider_name
        if provider_name == "deepseek":
            api_key = settings.DEEPSEEK_API_KEY
            base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        elif provider_name == "kimi":
            api_key = settings.KIMI_API_KEY
            base_url = settings.KIMI_BASE_URL.rstrip("/")
        elif provider_name == "qwen":
            api_key = settings.QWEN_API_KEY
            base_url = settings.QWEN_BASE_URL.rstrip("/")
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        body = {
            "model": config.model or self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in custom_msgs],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": True,
        }

        with httpx.Client(timeout=300.0) as client:
            with client.stream(
                "POST", f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                chunk = ChatGenerationChunk(
                                    message=AIMessageChunk(content=delta["content"])
                                )
                                if run_manager:
                                    run_manager.on_llm_new_token(delta["content"], chunk=chunk)
                                yield chunk
                        except json.JSONDecodeError:
                            continue

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """异步流式生成"""
        provider = self._get_provider()
        custom_msgs = _langchain_to_custom(messages)

        config = LLMConfig(
            model=kwargs.get("model_override", self.model_name),
            max_tokens=kwargs.get("max_tokens_override", self.max_tokens),
            temperature=kwargs.get("temperature_override", self.temperature),
            top_p=self.top_p,
        )

        async for token in provider.generate_stream(custom_msgs, config):
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=token))
            if run_manager:
                await run_manager.on_llm_new_token(token, chunk=chunk)
            yield chunk


# ---------------------------------------------------------------------------
# 便捷工厂函数
# ---------------------------------------------------------------------------

def create_chat_model(
    provider: str = "deepseek",
    model: Optional[str] = None,
    max_tokens: int = 16000,
    temperature: float = 0.7,
) -> NovelWriterChatModel:
    """创建 NovelWriterChatModel 实例的便捷函数。

    Args:
        provider: 'deepseek' | 'kimi' | 'qwen'
        model: 模型名，默认根据 provider 自动选择
        max_tokens: 最大输出 token
        temperature: 采样温度

    Returns:
        配置好的 NovelWriterChatModel
    """
    default_models = {
        "deepseek": "deepseek-chat",
        "kimi": "moonshot-v1-8k",
        "qwen": "qwen-turbo",
    }
    return NovelWriterChatModel(
        provider_name=provider,
        model_name=model or default_models.get(provider, "deepseek-chat"),
        max_tokens=max_tokens,
        temperature=temperature,
    )
