from sqlalchemy import Column, String, Integer, Text, ForeignKey

from app.models.base import Base, TimestampMixin


class MemoryRule(Base, TimestampMixin):
    __tablename__ = "memory_rules"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)

    category = Column(String(50))  # anti-ai / writer-style
    pattern = Column(Text, default="")
    replacement = Column(Text, default="")

    source = Column(String(50))  # community / project / session
    priority = Column(Integer, default=5)
