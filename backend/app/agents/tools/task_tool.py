"""借鉴 deep-agents-from-scratch 的 task() 委托工具。上下文隔离是关键设计。"""
from app.agents.base import BaseAgent

# 将在 init_agents() 中填充
_agent_registry: dict[str, BaseAgent] = {}


def set_registry(registry: dict):
    global _agent_registry
    _agent_registry = registry


async def task(description: str, subagent_type: str, files: dict[str, str] | None = None) -> dict:
    """委托子Agent执行任务。子Agent获得隔离的上下文（看不到主编历史）。"""
    if subagent_type not in _agent_registry:
        return {"content": f"Unknown agent: {subagent_type}", "files": {}, "error": True}

    agent = _agent_registry[subagent_type]
    try:
        result = await agent.run(task=description, files=files or {})
    except NotImplementedError:
        return {"content": f"Agent {subagent_type} not yet implemented", "files": {}, "error": True}

    # 透传 Agent 的所有字段，让调用方自行提取
    output = dict(result)
    output["error"] = False
    return output
