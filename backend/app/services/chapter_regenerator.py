"""章节重写 — 根据分析建议重新生成"""
from app.agents import get_agent


async def regenerate_chapter(original_content: str, feedback: str,
                             writing_plan: str, mode: str = "full") -> dict:
    """mode: full(全章重写) / partial(局部修改) / structure(结构调整)"""
    writer = get_agent("writer")
    if not writer:
        return {"content": "Writer not available", "passed": False}

    task = f"""原文:
{original_content}

修改要求 ({mode}):
{feedback}

写作计划:
{writing_plan}

请根据修改要求重写。"""

    if mode == "partial":
        task = f"请只修改以下部分，保持其余不变。\n{task}"

    return await writer.run(task=task)
