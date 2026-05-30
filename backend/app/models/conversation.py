from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from app.models.base import Base, TimestampMixin

class ConversationMessage(Base, TimestampMixin):
    __tablename__ = "conversation_messages"
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    session_id = Column(String(36), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
