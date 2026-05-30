from datetime import datetime
from pydantic import BaseModel, field_serializer

class WorldElementCreate(BaseModel):
    element_type: str  # location/magic_system/technology/culture/religion/faction/item
    name: str
    description: str = ""
    details: dict | None = None
    parent_id: str | None = None
    tags: list[str] | None = None
    importance: int = 5

class WorldElementUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    details: dict | None = None
    parent_id: str | None = None
    tags: list[str] | None = None
    importance: int | None = None

class WorldElementResponse(BaseModel):
    id: str
    novel_id: str
    element_type: str
    name: str
    description: str | None = None
    details: dict | None = None
    parent_id: str | None = None
    tags: list | None = None
    importance: int = 5
    created_at: datetime | None = None
    @field_serializer("created_at")
    def serialize_dt(self, v): return v.isoformat() if v else None
    model_config = {"from_attributes": True}
