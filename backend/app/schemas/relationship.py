from datetime import datetime
from pydantic import BaseModel, field_serializer

class RelationshipCreate(BaseModel):
    source_char_id: str; target_char_id: str
    rel_type: str = "neutral"; description: str = ""

class RelationshipResponse(BaseModel):
    id: str; novel_id: str; source_char_id: str; target_char_id: str
    rel_type: str | None = None; description: str | None = None
    history: list | None = None; created_at: datetime | None = None
    @field_serializer("created_at")
    def serialize_dt(self, v): return v.isoformat() if v else None
    model_config = {"from_attributes": True}
