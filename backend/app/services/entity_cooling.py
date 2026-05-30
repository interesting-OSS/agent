"""实体冷却管理 — 核心永不冷却 / 主要6章降温12章冷藏 / 次要3章降温8章冷藏"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.character import Character


async def get_active_characters(novel_id: str, current_chapter: int, db: AsyncSession) -> list[Character]:
    """返回当前应活跃的角色"""
    chars = (await db.execute(select(Character).where(Character.novel_id == novel_id))).scalars().all()
    active = []
    for c in chars:
        if c.importance >= 9:  # 核心
            active.append(c)
        elif c.importance >= 7:  # 主要
            last_seen = _get_last_appearance(c, current_chapter)
            if last_seen is None or current_chapter - last_seen < 6:
                active.append(c)
        else:  # 次要
            last_seen = _get_last_appearance(c, current_chapter)
            if last_seen is None or current_chapter - last_seen < 3:
                active.append(c)
    return active


def _get_last_appearance(char: Character, current_chapter: int) -> int | None:
    state = char.current_state or {}
    return state.get("last_chapter")


async def update_appearances(characters: list[Character], current_chapter: int, db: AsyncSession):
    """更新角色最后出场章节"""
    for c in characters:
        state = c.current_state or {}
        state["last_chapter"] = current_chapter
        c.current_state = state
    await db.commit()
