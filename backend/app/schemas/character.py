from datetime import datetime
from pydantic import BaseModel, field_serializer


class CharacterCreate(BaseModel):
    name: str
    role: str = "supporting"  # protagonist / antagonist / supporting / minor
    layer1_worldview: str = ""
    layer2_identity: str = ""
    layer3_values: str = ""
    layer4_abilities: str = ""
    layer5_skills: str = ""
    layer6_environment: str = ""
    career_id: str | None = None
    importance: int = 5


class CharacterUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    layer1_worldview: str | None = None
    layer2_identity: str | None = None
    layer3_values: str | None = None
    layer4_abilities: str | None = None
    layer5_skills: str | None = None
    layer6_environment: str | None = None
    career_id: str | None = None
    current_stage: int | None = None
    importance: int | None = None


class CharacterResponse(BaseModel):
    id: str
    novel_id: str
    name: str
    role: str | None = None
    layer1_worldview: str | None = None
    layer2_identity: str | None = None
    layer3_values: str | None = None
    layer4_abilities: str | None = None
    layer5_skills: str | None = None
    layer6_environment: str | None = None
    career_id: str | None = None
    current_stage: int = 0
    current_state: dict | None = None
    importance: int = 5
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_dt(self, v: datetime | None) -> str | None:
        return v.isoformat() if v else None

    model_config = {"from_attributes": True}
