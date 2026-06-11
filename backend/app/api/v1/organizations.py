from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.organization import Organization, OrganizationMember
from app.models.novel import Novel
from app.schemas.organization import OrganizationCreate, OrganizationResponse, MemberCreate, MemberResponse

router = APIRouter()

async def _verify_novel_exists(novel_id: str, db: AsyncSession):
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    if not r.scalar(): raise HTTPException(404, "Novel not found")

@router.get("/{novel_id}/organizations", response_model=list[OrganizationResponse])
async def list_orgs(novel_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    return (await db.execute(select(Organization).where(Organization.novel_id == novel_id))).scalars().all()

@router.post("/{novel_id}/organizations", response_model=OrganizationResponse, status_code=201)
async def create_org(novel_id: str, data: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    org = Organization(novel_id=novel_id, **data.model_dump())
    db.add(org); await db.commit(); await db.refresh(org)
    return org

@router.delete("/{novel_id}/organizations/{org_id}", status_code=204)
async def delete_org(novel_id: str, org_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    r = await db.execute(select(Organization).where(Organization.id == org_id, Organization.novel_id == novel_id))
    if not (org := r.scalar()): raise HTTPException(404, "Not found")
    await db.delete(org); await db.commit()

@router.get("/{novel_id}/organizations/{org_id}/members", response_model=list[MemberResponse])
async def list_members(novel_id: str, org_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    return (await db.execute(select(OrganizationMember).where(OrganizationMember.organization_id == org_id))).scalars().all()

@router.post("/{novel_id}/organizations/{org_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(novel_id: str, org_id: str, data: MemberCreate, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    m = OrganizationMember(organization_id=org_id, **data.model_dump(exclude={"organization_id"}))
    db.add(m); await db.commit(); await db.refresh(m)
    return m

@router.delete("/{novel_id}/organizations/{org_id}/members/{member_id}", status_code=204)
async def remove_member(novel_id: str, org_id: str, member_id: str, db: AsyncSession = Depends(get_db)):
    await _verify_novel_exists(novel_id, db)
    r = await db.execute(select(OrganizationMember).where(OrganizationMember.id == member_id, OrganizationMember.organization_id == org_id))
    if not (m := r.scalar()): raise HTTPException(404, "Not found")
    await db.delete(m); await db.commit()
