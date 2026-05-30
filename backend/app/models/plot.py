from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PlotArc(Base, TimestampMixin):
    __tablename__ = "plot_arcs"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    arc_number = Column(Integer, nullable=False)
    status = Column(String(20), default="planned")

    novel = relationship("Novel", back_populates="plot_arcs")


class PlotEvent(Base, TimestampMixin):
    __tablename__ = "plot_events"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    arc_id = Column(String(36), ForeignKey("plot_arcs.id"), nullable=True)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, default="")

    # major_plot / minor_plot / character_development / world_reveal
    event_type = Column(String(50))

    importance = Column(Integer, default=5)
    sequence_order = Column(Integer, nullable=False)

    characters_involved = Column(JSON, default=list)
    prerequisites = Column(JSON, default=list)
    consequences = Column(Text, default="")
    is_resolved = Column(Boolean, default=False)

    novel = relationship("Novel", back_populates="plot_events")


class OutlineNode(Base, TimestampMixin):
    __tablename__ = "outline_nodes"

    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    parent_id = Column(String(36), ForeignKey("outline_nodes.id"), nullable=True)

    title = Column(String(255), nullable=False)
    node_type = Column(String(20), default="chapter")  # volume / block / chapter
    sequence_order = Column(Integer, nullable=False)
    causal_sentence = Column(Text, default="")  # 因果句
    structure = Column(JSON, default=dict)         # 详细结构
