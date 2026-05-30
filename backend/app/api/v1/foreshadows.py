from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.foreshadow import Foreshadow
from app.models.novel import Novel
from app.services.foreshadow_service import detect_foreshadows, check_resolutions, get_foreshadow_reminders
from app.llm.registry import get_provider

router = APIRouter()

async def _verify(novel_id: str, request: Request, db: AsyncSession):
    uid = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == uid))
    if not r.scalar(): raise HTTPException(404)

@router.get("/{novel_id}/foreshadows")
async def list_fs(novel_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify(novel_id, request, db)
    return (await db.execute(select(Foreshadow).where(Foreshadow.novel_id == novel_id))).scalars().all()

@router.post("/{novel_id}/foreshadows", status_code=201)
async def create_fs(novel_id: str, data: dict, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify(novel_id, request, db)
    allowed_fields = {"title", "content", "keywords", "status", "planted_chapter", "target_chapter", "stable_id"}
    safe_data = {k: v for k, v in data.items() if k in allowed_fields}
    fs = Foreshadow(novel_id=novel_id, **safe_data)
    db.add(fs); await db.commit(); await db.refresh(fs)
    return fs

@router.post("/{novel_id}/foreshadows/{fs_id}/resolve")
async def resolve_fs(novel_id: str, fs_id: str, data: dict, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify(novel_id, request, db)
    r = await db.execute(select(Foreshadow).where(Foreshadow.id == fs_id, Foreshadow.novel_id == novel_id))
    if not (fs := r.scalar()): raise HTTPException(404)
    fs.status = "resolved"; fs.resolved_chapter = data.get("chapter_number")
    await db.commit(); return {"ok": True}

@router.post("/{novel_id}/chapters/{chapter_id}/detect-foreshadows")
async def detect_chapter_fs(novel_id: str, chapter_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify(novel_id, request, db)
    from app.models.chapter import Chapter
    ch = (await db.execute(select(Chapter).where(Chapter.id == chapter_id, Chapter.novel_id == novel_id))).scalar()
    if not ch: raise HTTPException(404)
    provider = get_provider("qwen")
    found = await detect_foreshadows(chapter_id, ch.content, db, provider)
    resolved = await check_resolutions(chapter_id, ch.content, db)
    reminders = await get_foreshadow_reminders(novel_id, ch.chapter_number, db)
    return {"detected": len(found), "resolved": len(resolved), "reminders": reminders}
