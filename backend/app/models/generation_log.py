from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey

from app.models.base import Base, TimestampMixin


class GenerationLog(Base, TimestampMixin):
    __tablename__ = "generation_logs"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=True)

    # chapter_generation / revision / summarization / world_building
    operation = Column(String(50), nullable=False)

    provider = Column(String(50), nullable=False)  # deepseek / kimi / qwen
    model = Column(String(100), nullable=False)

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    success = Column(Boolean, default=True)
    error_message = Column(Text, default="")
