from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.career import Career
from app.models.novel import Novel
from app.schemas.career import CareerCreate, CareerResponse

router = APIRouter()

async def _verify_novel_exists(novel_id: str, db: AsyncSession):
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    if not r.scalar(): raise HTTPException(404, "Novel not found")

@router.get("/{novel_id}/careers", response_model=list[CareerResponse])
async def list_careers(novel_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    return (await db.execute(select(Career).where(Career.novel_id == novel_id))).scalars().all()

@router.post("/{novel_id}/careers", response_model=CareerResponse, status_code=201)
async def create_career(novel_id: str, data: CareerCreate, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    c = Career(novel_id=novel_id, **data.model_dump())
    db.add(c); await db.commit(); await db.refresh(c)
    return c

@router.get("/{novel_id}/careers/{career_id}", response_model=CareerResponse)
async def get_career(novel_id: str, career_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    r = await db.execute(select(Career).where(Career.id == career_id, Career.novel_id == novel_id))
    if not (c := r.scalar()): raise HTTPException(404, "Not found")
    return c

@router.delete("/{novel_id}/careers/{career_id}", status_code=204)
async def delete_career(novel_id: str, career_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    r = await db.execute(select(Career).where(Career.id == career_id, Career.novel_id == novel_id))
    if not (c := r.scalar()): raise HTTPException(404, "Not found")
    await db.delete(c); await db.commit()

@router.post("/{novel_id}/careers/generate", response_model=CareerResponse, status_code=201)
async def generate_career(novel_id: str, db: AsyncSession = Depends(get_db)):
    """AI 根据类型自动生成职业体系"""
    await _verify_novel_exists(novel_id, db)
    from app.services.career_service import generate_career_system
    from app.llm.registry import get_provider
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = r.scalar()
    career = await generate_career_system(novel_id, novel.genre_id or "xianxia", get_provider("deepseek"))
    db.add(career); await db.commit(); await db.refresh(career)
    return career
