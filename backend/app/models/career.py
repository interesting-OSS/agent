from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Career(Base, TimestampMixin):
    __tablename__ = "careers"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    name = Column(String(255), nullable=False)
    stages = Column(JSON, default=list)  # [{name, features, power_range, social_status}, ...]
    max_stage = Column(Integer, default=10)

    novel = relationship("Novel", back_populates="careers")
    characters = relationship("Character", back_populates="career")
