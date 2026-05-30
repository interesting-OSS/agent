from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class LLMMessage:
    role: str       # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMConfig:
    model: str
    max_tokens: int = 16000
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict  # {prompt_tokens, completion_tokens}


@dataclass
class LLMTool:
    name: str
    description: str
    parameters: dict  # JSON Schema


class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(
        self, messages: list[LLMMessage], config: LLMConfig,
        tools: list[LLMTool] | None = None,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def generate_stream(
        self, messages: list[LLMMessage], config: LLMConfig,
        tools: list[LLMTool] | None = None,
    ) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def count_tokens(self, messages: list[LLMMessage], model: str) -> int:
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        ...
