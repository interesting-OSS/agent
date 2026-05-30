from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from app.models.base import Base, TimestampMixin

class AnalysisReport(Base, TimestampMixin):
    __tablename__ = "analysis_reports"
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=False)
    dimensions = Column(JSON, default=list)
    verdict = Column(String(20))
    suggestions = Column(JSON, default=list)
    raw_response = Column(Text, default="")
