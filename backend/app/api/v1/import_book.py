from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.llm.registry import get_provider
from app.services.book_import import import_book

router = APIRouter()

@router.post("/books/import")
async def import_book_endpoint(request: Request, file: UploadFile = File(...)):
    uid = await get_current_user_id(request)
    content = (await file.read()).decode("utf-8", errors="replace")
    provider = get_provider("deepseek")
    result = await import_book(content, provider)
    return result
