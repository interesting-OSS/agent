import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.sqlite import CHAR as UUIDChar
from sqlalchemy.orm import DeclarativeBase


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    id = Column(String(36), primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
