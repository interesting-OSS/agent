from app.agents.guardian import GuardianAgent, GUARDIAN_SYSTEM_PROMPT
from app.agents.custodian import CustodianAgent, CUSTODIAN_SYSTEM_PROMPT
from app.agents.supervisor import SupervisorAgent, SUPERVISOR_SYSTEM_PROMPT
from app.agents.architect import ArchitectAgent, ARCHITECT_SYSTEM_PROMPT
from app.agents.writer import WriterAgent, WRITER_SYSTEM_PROMPT
from app.agents.inspector import InspectorAgent, INSPECTOR_SYSTEM_PROMPT
from app.llm.registry import get_provider

AGENT_REGISTRY: dict[str, object] = {}

AGENT_CONFIGS = {
    "guardian": {
        "agent_class": GuardianAgent, "provider": "qwen",
        "name": "genre-guardian", "description": "类型合规检查", "system_prompt": GUARDIAN_SYSTEM_PROMPT,
        "tools": ["think_tool", "scan_forbidden_terms", "mark_issues"], "model": "qwen-turbo", "max_tokens": 6000,
    },
    "custodian": {
        "agent_class": CustodianAgent, "provider": "qwen",
        "name": "character-custodian", "description": "角色一致性守护", "system_prompt": CUSTODIAN_SYSTEM_PROMPT,
        "tools": ["think_tool", "check_consistency"], "model": "qwen-turbo", "max_tokens": 10000,
    },
    "supervisor": {
        "agent_class": SupervisorAgent, "provider": "deepseek",
        "name": "supervisor", "description": "小说创作主编", "system_prompt": SUPERVISOR_SYSTEM_PROMPT,
        "tools": ["write_todos", "read_todos", "task", "read_file", "write_file", "think_tool"],
        "model": "deepseek-chat", "max_tokens": 12000,
    },
    "architect": {
        "agent_class": ArchitectAgent, "provider": "deepseek",
        "name": "plot-architect", "description": "情节逻辑分析", "system_prompt": ARCHITECT_SYSTEM_PROMPT,
        "tools": ["think_tool", "search_foreshadows", "check_timeline", "check_causality"],
        "model": "deepseek-chat", "max_tokens": 15000,
    },
    "writer": {
        "agent_class": WriterAgent, "provider": "deepseek",
        "name": "prose-writer", "description": "正文写手，生成章节正文", "system_prompt": WRITER_SYSTEM_PROMPT,
        "tools": [], "model": "deepseek-chat", "max_tokens": 40000,
    },
    "inspector": {
        "agent_class": InspectorAgent, "provider": "kimi",
        "name": "quality-inspector", "description": "质量检查官", "system_prompt": INSPECTOR_SYSTEM_PROMPT,
        "tools": ["think_tool", "scan_forbidden_terms", "check_consistency"],
        "model": "moonshot-v1-8k", "max_tokens": 15000,
    },
}


def init_agents():
    from app.agents.base import SubAgentConfig
    for key, cfg in AGENT_CONFIGS.items():
        AGENT_REGISTRY[key] = cfg["agent_class"](
            SubAgentConfig(
                name=cfg["name"], description=cfg["description"],
                system_prompt=cfg["system_prompt"], tools=cfg.get("tools", []),
                model=cfg.get("model", "deepseek-chat"), max_tokens=cfg.get("max_tokens", 16000),
            ),
            provider=get_provider(cfg["provider"]),
        )
    from app.agents.tools.task_tool import set_registry
    set_registry(AGENT_REGISTRY)


def get_agent(name: str):
    if not AGENT_REGISTRY:
        init_agents()
    return AGENT_REGISTRY.get(name)
