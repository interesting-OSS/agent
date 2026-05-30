from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.novel import Novel
from app.models.chapter import Chapter, ChapterVersion
from app.services.chapter_regenerator import regenerate_chapter

router = APIRouter()

@router.post("/{novel_id}/chapters/{chapter_id}/revise")
async def revise_chapter(novel_id: str, chapter_id: str, data: dict, request: Request, db: AsyncSession = Depends(get_db)):
    uid = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == uid))
    if not r.scalar(): raise HTTPException(404)
    ch = (await db.execute(select(Chapter).where(Chapter.id == chapter_id, Chapter.novel_id == novel_id))).scalar()
    if not ch: raise HTTPException(404)

    # Save current version
    versions = (await db.execute(
        select(ChapterVersion).where(ChapterVersion.chapter_id == chapter_id).order_by(ChapterVersion.version_number.desc())
    )).scalars().all()
    next_ver = (versions[0].version_number + 1) if versions else 1
    ver = ChapterVersion(chapter_id=chapter_id, version_number=next_ver,
                         content=ch.content, word_count=ch.word_count or 0,
                         change_summary="Revision requested")
    db.add(ver)

    result = await regenerate_chapter(ch.content, data.get("feedback", ""),
                                      data.get("writing_plan", ""), data.get("mode", "full"))
    ch.content = result.get("content", ch.content)
    if ch.content != ver.content:
        ch.word_count = len(ch.content)
    await db.commit()
    return {"content": ch.content, "word_count": ch.word_count}

@router.get("/{novel_id}/chapters/{chapter_id}/versions")
async def list_versions(novel_id: str, chapter_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == uid))
    if not r.scalar(): raise HTTPException(404)
    vers = (await db.execute(
        select(ChapterVersion).where(ChapterVersion.chapter_id == chapter_id).order_by(ChapterVersion.version_number.desc())
    )).scalars().all()
    return [{"version_number": v.version_number, "word_count": v.word_count, "change_summary": v.change_summary,
             "model_used": v.model_used, "created_at": v.created_at.isoformat() if v.created_at else None} for v in vers]
