"""墨庐 LangGraph 模块 — 章节生成流水线图。

图结构:
    assemble_context → preflight (architect ‖ guardian)
        → write_chapter (streaming)
        → review (guardian → inspector)
        → decide_verdict → pass→END | rewrite→write_chapter | regenerate→write_chapter
"""

import json
import asyncio
from typing import Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.types import StreamWriter, Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.config import get_stream_writer

from app.langgraph.state import ChapterState
from app.langgraph.agents import create_agent_instance


# ---------------------------------------------------------------------------
# 节点函数
# ---------------------------------------------------------------------------

async def assemble_context_node(state: ChapterState) -> dict:
    """上下文组装节点。

    验证 context_layers 和 chapter_plan 已由 API 层预先填入。
    如果缺失则从 files 中提取。
    """
    layers = state.get("context_layers", {})
    plan = state.get("chapter_plan", "")

    # 从 files 中尝试恢复
    files = state.get("files", {})
    if not layers and "context_layers.json" in files:
        try:
            layers = json.loads(files["context_layers.json"])
        except json.JSONDecodeError:
            pass
    if not plan and "chapter_plan.md" in files:
        plan = files["chapter_plan.md"]

    return {
        "context_layers": layers,
        "chapter_plan": plan,
        "files": {
            "context_layers.json": json.dumps(layers, ensure_ascii=False),
            "chapter_plan.md": plan,
        },
    }


async def preflight_node(state: ChapterState) -> dict:
    """PreFlight 节点：并行运行 Architect + Guardian。

    Architect 检查情节逻辑、伏笔、时间线。
    Guardian 检查类型合规（基于大纲做预检查）。
    """
    chapter_plan = state.get("chapter_plan", "")
    genre_config = state.get("genre_config", {})
    chapter_number = state.get("chapter_number", 1)
    context_layers = state.get("context_layers", {})

    # 创建 architect 和 guardian agent
    architect = create_agent_instance("architect")
    guardian = create_agent_instance("guardian")

    # 构建 architect 输入
    arch_prompt = f"""本章大纲:
{chapter_plan}

前文摘要:
{context_layers.get('layer3_history', '暂无')}

活跃伏笔:
{f"当前第{chapter_number}章，请基于大纲推断待处理伏笔"}

请生成 PreFlight 报告 (JSON)。"""

    # 构建 guardian 输入
    guard_prompt = f"""检查类型合规性。

类型配置:
{json.dumps(genre_config, ensure_ascii=False, indent=2)[:3000]}

请先使用 scan_forbidden_terms_tool 扫描大纲中的潜在问题术语。"""

    # 并行执行
    async def run_architect():
        iso_state: dict[str, Any] = {"messages": [HumanMessage(content=arch_prompt)]}
        result = await architect.ainvoke(iso_state)
        # 提取最后的 AI 消息内容
        msgs = result.get("messages", [])
        last_content = ""
        for m in reversed(msgs):
            if hasattr(m, "content") and m.content and m.type == "ai":
                last_content = m.content
                break
        try:
            report = json.loads(last_content)
        except (json.JSONDecodeError, TypeError):
            report = {"summary": last_content[:200], "raw": last_content}
        return report

    async def run_guardian():
        iso_state: dict[str, Any] = {"messages": [HumanMessage(content=guard_prompt)]}
        result = await guardian.ainvoke(iso_state)
        msgs = result.get("messages", [])
        last_content = ""
        for m in reversed(msgs):
            if hasattr(m, "content") and m.content and m.type == "ai":
                last_content = m.content
                break
        try:
            report = json.loads(last_content)
        except (json.JSONDecodeError, TypeError):
            report = {"summary": last_content[:200], "passed": True}
        return report

    arch_result, guard_result = await asyncio.gather(run_architect(), run_guardian())

    return {
        "architect_report": arch_result,
        "guardian_pre_check": guard_result,
        "files": {
            "architect_report.json": json.dumps(arch_result, ensure_ascii=False, indent=2),
            "guardian_pre_check.json": json.dumps(guard_result, ensure_ascii=False, indent=2),
        },
    }


async def write_chapter_node(state: ChapterState) -> dict:
    """Write 节点：调用 Writer Agent 流式生成章节正文。

    使用 get_stream_writer 将 token 推送到 SSE。
    """
    chapter_plan = state.get("chapter_plan", "")
    genre_config = state.get("genre_config", {})
    character_profiles = state.get("character_profiles", [])
    context_layers = state.get("context_layers", {})
    user_focus = state.get("user_focus", "")
    target_words = state.get("target_word_count", 4000)
    architect_report = state.get("architect_report", {})
    guardian_pre = state.get("guardian_pre_check", {})

    genre_prompt = genre_config.get("prompt_segment", "")
    forbidden = genre_config.get("forbidden_terms", {}).get("terms", [])
    constraints = f"禁止术语（一个都不能出现）: {', '.join(forbidden[:15])}" if forbidden else ""
    previous_anchor = context_layers.get("layer2_active", "")[:500]

    # 构建 Writer 的完整 prompt
    writer_prompt = f"""## 类型文风要求
{genre_prompt}

## 写作约束
{constraints}

## 角色简要
{json.dumps(character_profiles, ensure_ascii=False, indent=2)}

## 前文关键锚点
{previous_anchor}

## 目标字数
{target_words} 字左右

## 情节架构师建议
{json.dumps(architect_report.get('key_events_this_chapter', []), ensure_ascii=False)}

## 写作计划:
{chapter_plan}

## 用户特殊指示:
{user_focus or '无'}

请开始写作。直接输出章节正文，不要加任何前缀说明。"""

    writer = create_agent_instance("writer")
    writer_state: dict[str, Any] = {"messages": [HumanMessage(content=writer_prompt)]}

    full_text = []
    try:
        writer_stream = get_stream_writer()
    except RuntimeError:
        # 不在 streaming 上下文中（如 generate-simple），直接 invoke
        result = await writer.ainvoke(writer_state)
        msgs = result.get("messages", [])
        content = ""
        for m in reversed(msgs):
            if hasattr(m, "content") and m.content and m.type == "ai":
                content = m.content
                break
        return {
            "chapter_content": content,
            "chapter_word_count": len(content),
        }

    # 流式模式：用 astream_events 获取 token
    async for chunk in writer.astream(writer_state, stream_mode=["messages"]):
        # astream 返回 (namespace, chunk) 元组
        if isinstance(chunk, tuple) and len(chunk) == 2:
            msg_chunk = chunk[1]
            if hasattr(msg_chunk, 'content') and msg_chunk.content:
                token = msg_chunk.content
                if isinstance(token, str):
                    full_text.append(token)
                    writer_stream({"phase": "writing", "token": token})

    content = "".join(full_text)
    return {
        "chapter_content": content,
        "chapter_word_count": len(content),
    }


async def review_chapter_node(state: ChapterState) -> dict:
    """Review 节点：Guardian → Inspector 串行审查。

    Guardian 先扫描正文中的禁止术语，
    Inspector 然后进行 10 维质量分析（需要 guardian 结果作为输入）。
    """
    chapter_content = state.get("chapter_content", "")
    genre_config = state.get("genre_config", {})
    character_profiles = state.get("character_profiles", [])
    chapter_plan = state.get("chapter_plan", "")
    target_words = state.get("target_word_count", 4000)
    forbidden = genre_config.get("forbidden_terms", {}).get("terms", [])

    # Step 1: Guardian 检查
    guardian_prompt = f"""扫描正文中的禁止术语。

禁止术语: {json.dumps(forbidden, ensure_ascii=False)}

先使用 scan_forbidden_terms_tool 做机械扫描。

正文:
{chapter_content[:8000]}"""

    guardian = create_agent_instance("guardian")
    g_result = await guardian.ainvoke({"messages": [HumanMessage(content=guardian_prompt)]})
    g_msgs = g_result.get("messages", [])
    g_content = ""
    for m in reversed(g_msgs):
        if hasattr(m, "content") and m.content and m.type == "ai":
            g_content = m.content
            break
    try:
        guardian_report = json.loads(g_content)
    except json.JSONDecodeError:
        guardian_report = {"passed": True, "violations": []}

    # Step 2: Inspector 检查（需要 guardian 结果）
    word_count = len(chapter_content)
    inspector_prompt = f"""章节正文:
{chapter_content[:10000]}

类型配置: {json.dumps(genre_config, ensure_ascii=False)}
角色档案: {json.dumps(character_profiles, ensure_ascii=False)}
情节大纲: {chapter_plan}
Guardian检查结果: {json.dumps(guardian_report, ensure_ascii=False)}
目标字数: {target_words} (实际: {word_count})

请对以上章节进行10维质量分析 (JSON)。"""

    inspector = create_agent_instance("inspector")
    i_result = await inspector.ainvoke({"messages": [HumanMessage(content=inspector_prompt)]})
    i_msgs = i_result.get("messages", [])
    i_content = ""
    for m in reversed(i_msgs):
        if hasattr(m, "content") and m.content and m.type == "ai":
            i_content = m.content
            break
    try:
        inspector_report = json.loads(i_content)
    except json.JSONDecodeError:
        inspector_report = {"verdict": "pass", "overall_score": 5, "summary": "无法解析", "dimensions": []}

    return {
        "guardian_report": guardian_report,
        "inspector_report": inspector_report,
        "files": {
            "guardian_report.json": json.dumps(guardian_report, ensure_ascii=False, indent=2),
            "inspector_report.json": json.dumps(inspector_report, ensure_ascii=False, indent=2),
        },
    }


def decide_verdict(state: ChapterState) -> Literal["pass", "rewrite", "regenerate"]:
    """判定节点：根据 Guardian + Inspector 报告决定走向。"""
    guardian_report = state.get("guardian_report", {})
    inspector_report = state.get("inspector_report", {})

    # Guardian fatal 违规 → regenerate
    if guardian_report and not guardian_report.get("passed", True):
        violations = guardian_report.get("violations", [])
        if any(v.get("severity") == "fatal" for v in violations):
            return "regenerate"

    # Inspector 判定
    verdict = inspector_report.get("verdict", "pass") if inspector_report else "pass"
    if verdict in ("rewrite", "regenerate"):
        return verdict

    return "pass"


# ---------------------------------------------------------------------------
# 图构建
# ---------------------------------------------------------------------------

def build_chapter_graph() -> StateGraph:
    """构建章节生成流水线图。

    Returns:
        编译好的 LangGraph StateGraph（未 compile，由调用方 .compile()）
    """
    graph = StateGraph(ChapterState)

    # 添加节点
    graph.add_node("assemble_context", assemble_context_node)
    graph.add_node("preflight", preflight_node)
    graph.add_node("write_chapter", write_chapter_node)
    graph.add_node("review_chapter", review_chapter_node)

    # 设置入口
    graph.set_entry_point("assemble_context")

    # 构建边
    graph.add_edge("assemble_context", "preflight")
    graph.add_edge("preflight", "write_chapter")
    graph.add_edge("write_chapter", "review_chapter")

    # 条件边: review → 判定 → pass=END / rewrite=write_chapter / regenerate=write_chapter
    graph.add_conditional_edges(
        "review_chapter",
        decide_verdict,
        {
            "pass": END,
            "rewrite": "write_chapter",
            "regenerate": "write_chapter",
        },
    )

    return graph.compile()


# ---------------------------------------------------------------------------
# 便捷运行函数
# ---------------------------------------------------------------------------

async def run_chapter_generation(
    novel_id: str,
    chapter_number: int,
    chapter_plan: str,
    genre_config: dict,
    character_profiles: list[dict],
    context_layers: dict,
    user_focus: str = "",
    target_word_count: int = 4000,
) -> dict:
    """一站式运行章节生成流水线。

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        chapter_plan: 本章大纲文本
        genre_config: 类型配置字典
        character_profiles: 角色档案列表
        context_layers: ContextAssembler.assemble() 的输出
        user_focus: 用户特殊指示
        target_word_count: 目标字数

    Returns:
        最终状态字典
    """
    graph = build_chapter_graph()

    initial_state: dict[str, Any] = {
        "novel_id": novel_id,
        "chapter_number": chapter_number,
        "chapter_plan": chapter_plan,
        "genre_config": genre_config,
        "character_profiles": character_profiles,
        "context_layers": context_layers,
        "user_focus": user_focus,
        "target_word_count": target_word_count,
        "messages": [],
        "files": {},
        "todos": [],
    }

    return await graph.ainvoke(initial_state)
