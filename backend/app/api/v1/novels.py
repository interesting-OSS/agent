from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.novel import Novel
from app.schemas.novel import NovelCreate, NovelUpdate, NovelResponse

router = APIRouter()


async def _get_user_id(request: Request) -> str:
    return await get_current_user_id(request)


@router.get("", response_model=list[NovelResponse])
async def list_novels(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request)
    result = await db.execute(
        select(Novel).where(Novel.user_id == user_id).order_by(Novel.updated_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=NovelResponse, status_code=201)
async def create_novel(
    data: NovelCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request)
    novel = Novel(
        user_id=user_id,
        title=data.title,
        genre_id=data.genre_id,
        genre_config={},           # Step 5 填充
        writing_style=data.writing_style,
        target_word_count=data.target_word_count,
    )
    db.add(novel)
    await db.commit()
    await db.refresh(novel)
    return novel


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request)
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id, Novel.user_id == user_id)
    )
    novel = result.scalar()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return novel


@router.patch("/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: str,
    data: NovelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request)
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id, Novel.user_id == user_id)
    )
    novel = result.scalar()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(novel, key, val)
    await db.commit()
    await db.refresh(novel)
    return novel


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(
    novel_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request)
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id, Novel.user_id == user_id)
    )
    novel = result.scalar()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    await db.delete(novel)
    await db.commit()
