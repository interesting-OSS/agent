from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.novel import Novel
from app.services.export_service import export_novel

router = APIRouter()

async def _verify_novel_exists(novel_id: str, db: AsyncSession):
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    if not r.scalar(): raise HTTPException(404)

@router.get("/{novel_id}/export")
async def export_novel_endpoint(novel_id: str, fmt: str = Query("md"), db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)

    try:
        content = await export_novel(novel_id, fmt, db)
    except NotImplementedError as e:
        raise HTTPException(501, str(e))

    media_types = {"md": "text/markdown", "txt": "text/plain", "html": "text/html"}
    return PlainTextResponse(content.decode("utf-8") if isinstance(content, bytes) else content,
                             media_type=media_types.get(fmt, "application/octet-stream"),
                             headers={"Content-Disposition": f"attachment; filename=novel.{fmt}"})
