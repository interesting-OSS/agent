from datetime import datetime
from pydantic import BaseModel, field_serializer

class OrganizationCreate(BaseModel):
    name: str
    description: str = ""
    org_type: str = "faction"
    details: dict | None = None
    importance: int = 5

class OrganizationResponse(BaseModel):
    id: str; novel_id: str; name: str; description: str | None = None
    org_type: str | None = None; details: dict | None = None
    importance: int = 5; created_at: datetime | None = None
    @field_serializer("created_at")
    def serialize_dt(self, v): return v.isoformat() if v else None
    model_config = {"from_attributes": True}

class MemberCreate(BaseModel):
    organization_id: str; character_id: str
    role: str = "member"; joined_at_chapter: int | None = None

class MemberResponse(BaseModel):
    id: str; organization_id: str; character_id: str
    role: str | None = None; joined_at_chapter: int | None = None
    created_at: datetime | None = None
    @field_serializer("created_at")
    def serialize_dt(self, v): return v.isoformat() if v else None
    model_config = {"from_attributes": True}
