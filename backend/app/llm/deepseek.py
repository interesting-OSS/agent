import json
import httpx
from typing import AsyncIterator

from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig, LLMResponse, LLMTool
from app.config import settings


class DeepSeekProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, messages, config, tools=None):
        body = {
            "model": config.model or "deepseek-chat",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }
        if tools:
            body["tools"] = [{"type": "function", "function": {
                "name": t.name, "description": t.description, "parameters": t.parameters
            }} for t in tools]

        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        content = choice["message"].get("content", "") or ""

        # Handle tool calls in response
        if choice["message"].get("tool_calls"):
            parts = []
            for tc in choice["message"]["tool_calls"]:
                parts.append(json.dumps({"tool": tc["function"]["name"], "args": tc["function"]["arguments"]}))
            content = "\n".join(parts)

        return LLMResponse(
            content=content,
            model=data["model"],
            usage=data.get("usage", {}),
        )

    async def generate_stream(self, messages, config, tools=None) -> AsyncIterator[str]:
        body = {
            "model": config.model or "deepseek-chat",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": True,
        }
        async with self.client.stream(
            "POST", f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=body,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def count_tokens(self, messages, model):
        return sum(len(m.content) * 1.5 for m in messages)

    async def close(self):
        await self.client.aclose()

    def supports_tools(self):
        return True
