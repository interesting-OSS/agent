"""动态记忆学习 — diff分析 AI原稿 vs 作者修改稿"""
import difflib
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory_rule import MemoryRule
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig


def compute_diff(original: str, modified: str) -> list[dict]:
    """计算 AI 原稿与作者修改稿的 diff"""
    diff = list(difflib.unified_diff(original.splitlines(), modified.splitlines(), lineterm=""))
    changes = []
    for line in diff:
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            changes.append({"type": "removed", "text": line[1:]})
        elif line.startswith("+"):
            changes.append({"type": "added", "text": line[1:]})
    return changes


async def learn_from_edit(ai_draft: str, author_edit: str, novel_id: str,
                          provider: BaseLLMProvider, db: AsyncSession) -> list[MemoryRule]:
    """对比 AI 原稿和作者修改稿，提取修改模式"""
    changes = compute_diff(ai_draft, author_edit)
    if len(changes) < 3:
        return []

    messages = [
        LLMMessage(role="system", content="""分析 AI 写作修改,提取可复用规则。输出JSON数组:
[{"category":"anti-ai|writer-style","pattern":"被删文本的特征","replacement":"替换成的文本特征","priority":1-10}]"""),
        LLMMessage(role="user", content=f"AI原稿→作者修改的变化:\n{json.dumps(changes[:20], ensure_ascii=False, indent=2)}"),
    ]
    resp = await provider.generate(messages, LLMConfig(model="qwen-turbo", temperature=0.0, max_tokens=1000))
    try:
        patterns = json.loads(resp.content)
    except json.JSONDecodeError:
        return []

    rules = []
    for p in patterns:
        rule = MemoryRule(novel_id=novel_id, source="project",
                          category=p.get("category", "writer-style"),
                          pattern=p.get("pattern", ""),
                          replacement=p.get("replacement", ""),
                          priority=p.get("priority", 5))
        db.add(rule)
        rules.append(rule)
    await db.commit()
    return rules


async def get_applicable_rules(novel_id: str, db: AsyncSession) -> list[MemoryRule]:
    return (await db.execute(
        select(MemoryRule).where(MemoryRule.novel_id == novel_id).order_by(MemoryRule.priority.desc())
    )).scalars().all()
