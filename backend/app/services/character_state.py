from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.character import Character
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig
import json


async def update_character_states(
    novel_id: str,
    chapter_content: str,
    db: AsyncSession,
    provider: BaseLLMProvider | None = None,
):
    """每章归档后调用，调用 Custodian Agent 分析正文，更新角色当前状态"""
    characters = (await db.execute(
        select(Character).where(Character.novel_id == novel_id)
    )).scalars().all()

    if not characters or not provider:
        return

    char_map = {c.name: c for c in characters}
    messages = [
        LLMMessage(role="system", content="""分析以下章节正文，提取每个出场角色的状态变化。
输出严格JSON:
[
  {"name":"角色名","location":"...","emotion":"...","knowledge_changed":"...","relationship_changes":[...]}
]
只包括在正文中实际出场的角色。"""),
        LLMMessage(role="user", content=f"角色列表: {', '.join(char_map.keys())}\n\n正文:\n{chapter_content[:8000]}"),
    ]
    resp = await provider.generate(messages, LLMConfig(model="qwen-turbo", temperature=0.0, max_tokens=2000))
    try:
        updates = json.loads(resp.content)
    except json.JSONDecodeError:
        return

    for update in updates:
        name = update.get("name", "")
        if name in char_map:
            char = char_map[name]
            current = char.current_state or {}
            current.update({
                "location": update.get("location", current.get("location", "")),
                "emotion": update.get("emotion", current.get("emotion", "")),
                "knowledge": update.get("knowledge_changed", current.get("knowledge", "")),
            })
            char.current_state = current
    await db.commit()
