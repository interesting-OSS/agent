from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.novel import Novel
from app.services.export_service import export_novel

router = APIRouter()

@router.get("/{novel_id}/export")
async def export_novel_endpoint(novel_id: str, fmt: str = Query("md"),
                                request: Request = None, db: AsyncSession = Depends(get_db)):
    uid = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == uid))
    if not r.scalar(): raise HTTPException(404)

    try:
        content = await export_novel(novel_id, fmt, db)
    except NotImplementedError as e:
        raise HTTPException(501, str(e))

    media_types = {"md": "text/markdown", "txt": "text/plain", "html": "text/html"}
    return PlainTextResponse(content.decode("utf-8") if isinstance(content, bytes) else content,
                             media_type=media_types.get(fmt, "application/octet-stream"),
                             headers={"Content-Disposition": f"attachment; filename=novel.{fmt}"})
