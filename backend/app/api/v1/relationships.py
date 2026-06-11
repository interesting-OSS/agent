from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.relationship import CharacterRelationship
from app.models.novel import Novel
from app.schemas.relationship import RelationshipCreate, RelationshipResponse

router = APIRouter()

async def _verify_novel_exists(novel_id: str, db: AsyncSession):
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    if not r.scalar(): raise HTTPException(404, "Novel not found")

@router.get("/{novel_id}/relationships", response_model=list[RelationshipResponse])
async def list_rels(novel_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    return (await db.execute(select(CharacterRelationship).where(CharacterRelationship.novel_id == novel_id))).scalars().all()

@router.get("/{novel_id}/relationships/{char_id}", response_model=list[RelationshipResponse])
async def get_char_rels(novel_id: str, char_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    return (await db.execute(
        select(CharacterRelationship).where(
            CharacterRelationship.novel_id == novel_id,
            or_(CharacterRelationship.source_char_id == char_id, CharacterRelationship.target_char_id == char_id)
        )
    )).scalars().all()

@router.post("/{novel_id}/relationships", response_model=RelationshipResponse, status_code=201)
async def create_rel(novel_id: str, data: RelationshipCreate, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    rel = CharacterRelationship(novel_id=novel_id, **data.model_dump())
    db.add(rel); await db.commit(); await db.refresh(rel)
    return rel

@router.delete("/{novel_id}/relationships/{rel_id}", status_code=204)
async def delete_rel(novel_id: str, rel_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    r = await db.execute(select(CharacterRelationship).where(CharacterRelationship.id == rel_id, CharacterRelationship.novel_id == novel_id))
    if not (rel := r.scalar()): raise HTTPException(404, "Not found")
    await db.delete(rel); await db.commit()
