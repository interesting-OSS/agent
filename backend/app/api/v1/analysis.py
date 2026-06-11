from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.novel import Novel
from app.models.chapter import Chapter
from app.models.character import Character
from app.services.plot_analyzer import analyze_chapter
from app.genre import load_genre_config
import json

router = APIRouter()

async def _verify_novel_exists(novel_id: str, db: AsyncSession):
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    if not r.scalar(): raise HTTPException(404)

@router.get("/{novel_id}/analysis/{chapter_id}")
async def get_analysis(novel_id: str, chapter_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    ch = (await db.execute(select(Chapter).where(Chapter.id == chapter_id))).scalar()
    if not ch or not ch.content: raise HTTPException(404, "No content to analyze")

    novel = (await db.execute(select(Novel).where(Novel.id == novel_id))).scalar()
    genre_cfg = {}
    if novel.genre_id:
        try: genre_cfg = load_genre_config(novel.genre_id)
        except ValueError: pass
    chars = (await db.execute(select(Character).where(Character.novel_id == novel_id, Character.importance >= 5))).scalars().all()
    char_profiles = [{"name": c.name, "role": c.role, "layer4": c.layer4_abilities, "layer2": c.layer2_identity} for c in chars]

    result = await analyze_chapter(novel_id, chapter_id, ch.content,
                                   genre_config=json.dumps(genre_cfg, ensure_ascii=False),
                                   character_profiles=json.dumps(char_profiles, ensure_ascii=False))
    return result
