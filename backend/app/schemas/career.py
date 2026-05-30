from datetime import datetime
from pydantic import BaseModel, field_serializer


class CareerCreate(BaseModel):
    name: str
    stages: list[dict] = []
    max_stage: int = 10


class CareerResponse(BaseModel):
    id: str
    novel_id: str
    name: str
    stages: list[dict] | None = None
    max_stage: int = 10
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_dt(self, v: datetime | None) -> str | None:
        return v.isoformat() if v else None

    model_config = {"from_attributes": True}
