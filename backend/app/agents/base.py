from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict, NotRequired

from app.llm.base import BaseLLMProvider


class SubAgentConfig(TypedDict):
    name: str
    description: str
    system_prompt: str
    tools: NotRequired[list[str]]
    model: NotRequired[str]
    max_tokens: NotRequired[int]


@dataclass
class AgentContext:
    system_prompt: str
    task_description: str
    files: dict[str, str] = field(default_factory=dict)
    max_tokens: int = 16000


class BaseAgent(ABC):
    def __init__(self, config: SubAgentConfig, provider: BaseLLMProvider):
        self.config = config
        self.provider = provider

    async def run(self, task: str, files: dict[str, str] | None = None) -> dict:
        ctx = AgentContext(
            system_prompt=self.config["system_prompt"],
            task_description=task,
            files=files or {},
            max_tokens=self.config.get("max_tokens", 16000),
        )
        return await self._execute(ctx)

    @abstractmethod
    async def _execute(self, ctx: AgentContext) -> dict:
        ...
