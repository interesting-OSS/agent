from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    org_type = Column(String(50))  # faction / guild / family / kingdom / cult / company
    details = Column(JSON, default=dict)
    importance = Column(Integer, default=5)


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    character_id = Column(String(36), ForeignKey("characters.id"), nullable=False)
    role = Column(String(100))  # leader / member / affiliate / former
    joined_at_chapter = Column(Integer, nullable=True)
