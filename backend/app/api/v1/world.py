from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.world_element import WorldElement
from app.models.novel import Novel
from app.schemas.world import WorldElementCreate, WorldElementUpdate, WorldElementResponse

router = APIRouter()

async def _verify_owner(novel_id: str, request: Request, db: AsyncSession):
    user_id = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == user_id))
    if not r.scalar(): raise HTTPException(404, "Novel not found")

@router.get("/{novel_id}/world", response_model=list[WorldElementResponse])
async def list_elements(novel_id: str, element_type: str | None = Query(None), request: Request = None, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    q = select(WorldElement).where(WorldElement.novel_id == novel_id)
    if element_type: q = q.where(WorldElement.element_type == element_type)
    return (await db.execute(q)).scalars().all()

@router.post("/{novel_id}/world", response_model=WorldElementResponse, status_code=201)
async def create_element(novel_id: str, data: WorldElementCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    el = WorldElement(novel_id=novel_id, **data.model_dump())
    db.add(el); await db.commit(); await db.refresh(el)
    return el

@router.get("/{novel_id}/world/{el_id}", response_model=WorldElementResponse)
async def get_element(novel_id: str, el_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(WorldElement).where(WorldElement.id == el_id, WorldElement.novel_id == novel_id))
    if not (el := r.scalar()): raise HTTPException(404, "Not found")
    return el

@router.patch("/{novel_id}/world/{el_id}", response_model=WorldElementResponse)
async def update_element(novel_id: str, el_id: str, data: WorldElementUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(WorldElement).where(WorldElement.id == el_id, WorldElement.novel_id == novel_id))
    if not (el := r.scalar()): raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(el, k, v)
    await db.commit(); await db.refresh(el)
    return el

@router.delete("/{novel_id}/world/{el_id}", status_code=204)
async def delete_element(novel_id: str, el_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await _verify_owner(novel_id, request, db)
    r = await db.execute(select(WorldElement).where(WorldElement.id == el_id, WorldElement.novel_id == novel_id))
    if not (el := r.scalar()): raise HTTPException(404, "Not found")
    await db.delete(el); await db.commit()
