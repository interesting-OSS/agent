import json
import httpx
from typing import AsyncIterator

from app.llm.base import BaseLLMProvider, LLMResponse
from app.config import settings


class QwenProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.base_url = settings.QWEN_BASE_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, messages, config, tools=None):
        body = {
            "model": config.model or "qwen-turbo",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"].get("content", "") or "",
            model=data["model"],
            usage=data.get("usage", {}),
        )

    async def generate_stream(self, messages, config, tools=None) -> AsyncIterator[str]:
        body = {
            "model": config.model or "qwen-turbo",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
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
        return False
