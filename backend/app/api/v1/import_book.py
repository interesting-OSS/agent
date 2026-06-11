from fastapi import APIRouter, UploadFile, File
from app.llm.registry import get_provider
from app.services.book_import import import_book

router = APIRouter()

@router.post("/books/import")
async def import_book_endpoint(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="replace")
    provider = get_provider("deepseek")
    result = await import_book(content, provider)
    return result
