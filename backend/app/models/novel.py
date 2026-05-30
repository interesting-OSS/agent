from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Novel(Base, TimestampMixin):
    __tablename__ = "novels"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="draft")

    # 类型隔离系统 — Step 5 填充
    genre_id = Column(String(50))
    genre_config = Column(JSON, default=dict)

    # 写作风格
    writing_style = Column(String(50), default="plain")

    # 统计
    word_count = Column(Integer, default=0)
    target_word_count = Column(Integer)

    user = relationship("User", back_populates="novels")
    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan")
    careers = relationship("Career", back_populates="novel", cascade="all, delete-orphan")
    world_elements = relationship("WorldElement", back_populates="novel", cascade="all, delete-orphan")
    plot_arcs = relationship("PlotArc", back_populates="novel", cascade="all, delete-orphan")
    plot_events = relationship("PlotEvent", back_populates="novel", cascade="all, delete-orphan")
    foreshadows = relationship("Foreshadow", back_populates="novel", cascade="all, delete-orphan")
