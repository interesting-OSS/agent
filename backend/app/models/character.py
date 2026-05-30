from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Character(Base, TimestampMixin):
    __tablename__ = "characters"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(100))  # protagonist / antagonist / supporting / minor

    # 认知6层模型
    layer1_worldview = Column(Text, default="")
    layer2_identity = Column(Text, default="")
    layer3_values = Column(Text, default="")
    layer4_abilities = Column(Text, default="")
    layer5_skills = Column(Text, default="")
    layer6_environment = Column(Text, default="")

    # 职业阶段 — Step 6 填充
    career_id = Column(String(36), ForeignKey("careers.id"), nullable=True)
    current_stage = Column(Integer, default=0)

    # 当前状态追踪（每章更新）
    current_state = Column(JSON, default=dict)

    importance = Column(Integer, default=5)  # 1-10，影响实体冷却

    novel = relationship("Novel", back_populates="characters")
    career = relationship("Career", back_populates="characters")
