from sqlalchemy import Column, String, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    title = Column(String(255))
    chapter_number = Column(Integer, nullable=False)
    content = Column(Text, default="")
    summary = Column(Text, default="")

    # 状态机: outline → draft → generated → reviewed → finalized
    status = Column(String(20), default="outline")

    # 双模式生成 — Step 8 填充
    generation_mode = Column(String(10), default="1-1")
    expansion_plan = Column(JSON, default=dict)

    word_count = Column(Integer, default=0)
    review_notes = Column(Text, default="")

    __table_args__ = (UniqueConstraint("novel_id", "chapter_number"),)

    novel = relationship("Novel", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan")


class ChapterVersion(Base, TimestampMixin):
    __tablename__ = "chapter_versions"

    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    change_summary = Column(Text, default="")
    model_used = Column(String(100))
    tokens_used = Column(Integer)

    __table_args__ = (UniqueConstraint("chapter_id", "version_number"),)

    chapter = relationship("Chapter", back_populates="versions")
