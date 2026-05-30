from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CharacterRelationship(Base, TimestampMixin):
    __tablename__ = "character_relationships"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    source_char_id = Column(String(36), ForeignKey("characters.id"), nullable=False)
    target_char_id = Column(String(36), ForeignKey("characters.id"), nullable=False)

    # ally / enemy / family / mentor / lover / rival / neutral
    rel_type = Column(String(50))
    description = Column(Text, default="")
    history = Column(JSON, default=list)
