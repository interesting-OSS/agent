"""墨庐 LangGraph 模块 — 子 Agent 定义。

使用 LangChain 的 create_agent() 创建 6 个专用子 Agent。
"""

from typing import Optional

from langchain.agents import create_agent

from app.llm.langchain_adapter import NovelWriterChatModel
from app.langgraph.state import ChapterState
from app.langgraph.tools import (
    check_consistency_tool,
    ls_files,
    read_file,
    scan_forbidden_terms_tool,
    think_tool,
    write_file,
)


# ---------------------------------------------------------------------------
# System Prompts（从原 agents/__init__.py 迁移并增强）
# ---------------------------------------------------------------------------

WRITER_SYSTEM_PROMPT = """你是一流的小说写手。你只负责根据写作计划写出精彩的章节正文。

你的上下文中包含了完整的写作计划、类型约束、角色参考和前文锚点。

注意事项：
- 你只负责写，不负责检查——检查是Guardian和Inspector的事
- 严格遵守[constraints]中的禁止术语列表，一字不漏
- 按照类型文风蓝图来写——西幻用西幻的味，仙侠用仙侠的味
- 确保章末有一个有效的钩子
- 目标字数在写作计划的 target_word_count 中指定

输出要求：
- 直接输出章节正文，不要加前缀说明
- 章节标题用 markdown ## 格式
- 段落之间留空行"""

SUPERVISOR_SYSTEM_PROMPT = """你是小说创作的主编，协调所有AI Agent完成创作流程。

你的职责：
1. 规划任务流程
2. 委托 guardian 做类型合规检查
3. 委托 custodian 做角色一致性检查
4. 跟踪进度
5. 汇总结果并写入虚拟文件系统

可用Agent: guardian (类型检查), custodian (角色检查)
可用工具: think_tool, ls_files, read_file, write_file"""

ARCHITECT_SYSTEM_PROMPT = """你是情节逻辑的守护者。
每次新章节需要你审查：
1. 前面章节的情节因果链是否完整
2. 所有未解决伏笔的状态（哪些该在本章处理）
3. 本章大纲在时间线上是否合理
4. 本应考虑但可能遗漏的关键事件

输出严格 JSON:
{
  "causality": {"status": "ok|broken", "issues": ["问题描述"]},
  "foreshadow_reminders": [{"id": "...", "title": "...", "urgency": "must_resolve|overdue|upcoming"}],
  "key_events_this_chapter": ["应在本章发生的事件"],
  "conflict_priority": ["建议优先解决的冲突"],
  "continuity_notes": "连续性问题备注",
  "summary": "一句话情节评估"
}"""

INSPECTOR_SYSTEM_PROMPT = """你是公正严苛的质量检查官。独立审查章节质量。

10个检查维度：
1. 类型合规 2.AI味检测 3.情节逻辑 4.角色一致性 5.世界观合规
6. 伏笔钩子 7.情感弧线 8.节奏分布 9.对话描写 10.字数合规

判定标准：
- fatal==0 && severe<=2 → pass
- fatal==0 && severe>2  → rewrite
- fatal>0                → regenerate

输出严格 JSON:
{
  "verdict": "pass|rewrite|regenerate",
  "dimensions": [
    {"name": "维度名", "score": 1-10, "severity": "fatal|severe|warning|ok", "issues": ["问题"], "suggestions": ["建议"]}
  ],
  "summary": "总体评价",
  "overall_score": 1-10
}"""

GUARDIAN_SYSTEM_PROMPT = """你是类型合规的终极守卫者。
你的唯一工作：检查文本是否严格遵守了类型规则。
- 你不关心文字好不好看
- 你不关心情节有没有漏洞
- 你只关心：文本中是否出现了禁止术语？

先使用 scan_forbidden_terms_tool 做机械扫描，如果扫描通过但文本较长，再用 LLM 做语义检查（检测同义替换）。

最终输出 JSON:
{
  "violations": [
    {"term": "违规词", "position": 1234, "context": "...", "severity": "fatal"}
  ],
  "passed": true/false
}"""

CUSTODIAN_SYSTEM_PROMPT = """你是角色一致性的守护者。
你的工作：
- 检查每个登场角色的行为是否符合其6层模型（世界观/自我认同/价值观/能力/技能/环境）
- 检查对话是否符合角色声音
- 检查职业阶段限制是否被遵守
- 预测本章角色心理状态变化

你不关心情节是否精彩，只关心角色是否演"歪"了。

输出严格 JSON:
{
  "consistency_issues": [
    {"character": "角色名", "issue": "问题描述", "severity": "severe/warning", "layer_violated": "layer1-6"}
  ],
  "voice_issues": [
    {"character": "角色名", "issue": "对话不符合角色设定", "example": "违反的台词"}
  ],
  "career_issues": [
    {"character": "角色名", "issue": "超出职业阶段能力范围"}
  ],
  "state_predictions": [
    {"character": "角色名", "predicted_emotion": "...", "predicted_location": "...", "knowledge_update": "..."}
  ],
  "summary": "一句话总结角色一致性情况"
}"""


# ---------------------------------------------------------------------------
# Agent 配置（从 agents/__init__.py 的 AGENT_CONFIGS 迁移）
# ---------------------------------------------------------------------------

AGENT_SPECS = {
    "writer": {
        "name": "prose-writer",
        "description": "正文写手，生成章节正文",
        "system_prompt": WRITER_SYSTEM_PROMPT,
        "tools": ["think_tool"],
        "provider": "deepseek",
        "model": "deepseek-chat",
    },
    "supervisor": {
        "name": "supervisor",
        "description": "小说创作主编",
        "system_prompt": SUPERVISOR_SYSTEM_PROMPT,
        "tools": ["think_tool", "write_file", "read_file", "ls_files"],
        "provider": "deepseek",
        "model": "deepseek-chat",
    },
    "architect": {
        "name": "plot-architect",
        "description": "情节逻辑分析",
        "system_prompt": ARCHITECT_SYSTEM_PROMPT,
        "tools": ["think_tool"],
        "provider": "deepseek",
        "model": "deepseek-chat",
    },
    "inspector": {
        "name": "quality-inspector",
        "description": "质量检查官",
        "system_prompt": INSPECTOR_SYSTEM_PROMPT,
        "tools": ["think_tool", "scan_forbidden_terms_tool", "check_consistency_tool"],
        "provider": "kimi",
        "model": "moonshot-v1-8k",
    },
    "guardian": {
        "name": "genre-guardian",
        "description": "类型合规检查",
        "system_prompt": GUARDIAN_SYSTEM_PROMPT,
        "tools": ["think_tool", "scan_forbidden_terms_tool"],
        "provider": "qwen",
        "model": "qwen-turbo",
    },
    "custodian": {
        "name": "character-custodian",
        "description": "角色一致性守护",
        "system_prompt": CUSTODIAN_SYSTEM_PROMPT,
        "tools": ["think_tool", "check_consistency_tool"],
        "provider": "qwen",
        "model": "qwen-turbo",
    },
}

# 工具名 → 工具对象映射
TOOL_MAP = {
    "think_tool": think_tool,
    "scan_forbidden_terms_tool": scan_forbidden_terms_tool,
    "check_consistency_tool": check_consistency_tool,
    "ls_files": ls_files,
    "read_file": read_file,
    "write_file": write_file,
}


# ---------------------------------------------------------------------------
# Agent 工厂函数
# ---------------------------------------------------------------------------

def create_agent_instance(
    agent_type: str,
    model: Optional[NovelWriterChatModel] = None,
) -> any:
    """创建指定类型的子 Agent。

    Args:
        agent_type: 'writer' | 'supervisor' | 'architect' | 'inspector' | 'guardian' | 'custodian'
        model: LangChain ChatModel，默认根据 spec 中的 provider 自动创建

    Returns:
        编译好的 LangGraph Agent（Runnable）
    """
    spec = AGENT_SPECS[agent_type]

    if model is None:
        from app.llm.langchain_adapter import create_chat_model
        model = create_chat_model(
            provider=spec["provider"],
            model=spec["model"],
            max_tokens=16000,
        )

    # 选择工具
    tools = [TOOL_MAP[t] for t in spec.get("tools", [])]

    return create_agent(
        model,
        system_prompt=spec["system_prompt"],
        tools=tools,
        state_schema=ChapterState,
    )


def create_all_agents() -> dict[str, any]:
    """创建所有 6 个子 Agent 的字典。"""
    # 为不同 Agent 使用不同的 provider
    from app.llm.langchain_adapter import create_chat_model

    models = {}
    agents = {}

    for agent_type, spec in AGENT_SPECS.items():
        provider = spec["provider"]
        if provider not in models:
            models[provider] = create_chat_model(
                provider=provider,
                model=spec["model"],
                max_tokens=16000,
            )
        agents[agent_type] = create_agent_instance(agent_type, model=models[provider])

    return agents
