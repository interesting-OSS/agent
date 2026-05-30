from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from app.models.base import Base, TimestampMixin

class ContextSnapshot(Base, TimestampMixin):
    __tablename__ = "context_snapshots"
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=True)
    snapshot_type = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    token_estimate = Column(Integer)
