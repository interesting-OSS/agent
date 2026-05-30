from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class WorldElement(Base, TimestampMixin):
    __tablename__ = "world_elements"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)

    # location / magic_system / technology / culture / religion / faction / item
    element_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    details = Column(JSON, default=dict)

    parent_id = Column(String(36), ForeignKey("world_elements.id"), nullable=True)

    tags = Column(JSON, default=list)
    importance = Column(Integer, default=5)

    novel = relationship("Novel", back_populates="world_elements")
