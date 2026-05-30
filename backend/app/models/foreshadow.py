from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Foreshadow(Base, TimestampMixin):
    __tablename__ = "foreshadows"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    title = Column(String(255))
    content = Column(Text, default="")
    keywords = Column(JSON, default=list)

    # planned → planted → reminded → resolved → abandoned
    status = Column(String(20), default="planned")

    planted_chapter = Column(Integer, nullable=True)
    target_chapter = Column(Integer, nullable=True)
    resolved_chapter = Column(Integer, nullable=True)

    stable_id = Column(String(64), unique=True)

    novel = relationship("Novel", back_populates="foreshadows")
