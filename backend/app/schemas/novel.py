from datetime import datetime
from pydantic import BaseModel, field_serializer


class NovelCreate(BaseModel):
    title: str
    genre_id: str = ""
    writing_style: str = "plain"
    target_word_count: int | None = None


class NovelUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    writing_style: str | None = None
    target_word_count: int | None = None


class NovelResponse(BaseModel):
    id: str
    user_id: str
    title: str
    status: str
    genre_id: str | None = None
    writing_style: str = "plain"
    word_count: int = 0
    target_word_count: int | None = None
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, v: datetime | None) -> str | None:
        return v.isoformat() if v else None

    model_config = {"from_attributes": True}
