from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.character import Character
from app.models.novel import Novel
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse

router = APIRouter()

async def _verify_owner(novel_id: str, request: Request, db: AsyncSession):
    user_id = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == user_id))
    if not r.scalar():
        raise HTTPException(404, "Novel not found")

@router.get("/{novel_id}/characters", response_model=list[CharacterResponse])
async def list_chars(novel_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(Character).where(Character.novel_id == novel_id))
    return r.scalars().all()

@router.post("/{novel_id}/characters", response_model=CharacterResponse, status_code=201)
async def create_char(novel_id: str, data: CharacterCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    c = Character(novel_id=novel_id, **data.model_dump())
    db.add(c); await db.commit(); await db.refresh(c)
    return c

@router.get("/{novel_id}/characters/{char_id}", response_model=CharacterResponse)
async def get_char(novel_id: str, char_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(Character).where(Character.id == char_id, Character.novel_id == novel_id))
    if not (c := r.scalar()): raise HTTPException(404, "Not found")
    return c

@router.patch("/{novel_id}/characters/{char_id}", response_model=CharacterResponse)
async def update_char(novel_id: str, char_id: str, data: CharacterUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(Character).where(Character.id == char_id, Character.novel_id == novel_id))
    if not (c := r.scalar()): raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(c, k, v)
    await db.commit(); await db.refresh(c)
    return c

@router.delete("/{novel_id}/characters/{char_id}", status_code=204)
async def delete_char(novel_id: str, char_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(Character).where(Character.id == char_id, Character.novel_id == novel_id))
    if not (c := r.scalar()): raise HTTPException(404, "Not found")
    await db.delete(c); await db.commit()
