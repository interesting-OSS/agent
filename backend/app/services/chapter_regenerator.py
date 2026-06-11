"""章节重写 — 根据分析建议重新生成（已迁移到 LangGraph）"""
from langchain_core.messages import HumanMessage

from app.langgraph.agents import create_agent_instance


async def regenerate_chapter(original_content: str, feedback: str,
                             writing_plan: str, mode: str = "full") -> dict:
    """mode: full(全章重写) / partial(局部修改) / structure(结构调整)"""
    writer = create_agent_instance("writer")

    task = f"""原文:
{original_content}

修改要求 ({mode}):
{feedback}

写作计划:
{writing_plan}

请根据修改要求重写。"""

    if mode == "partial":
        task = f"请只修改以下部分，保持其余不变。\n{task}"

    result = await writer.ainvoke({"messages": [HumanMessage(content=task)]})
    msgs = result.get("messages", [])
    content = ""
    for m in reversed(msgs):
        if hasattr(m, "content") and m.content and m.type == "ai":
            content = m.content
            break

    return {"content": content, "passed": bool(content)}
