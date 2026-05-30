from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from app.models.base import Base, TimestampMixin

class SkillCoach(Base, TimestampMixin):
    __tablename__ = "skill_coaches"
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50))
    skill_md = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)
    is_public = Column(Boolean, default=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
