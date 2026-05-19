from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.db.session import Base


class Entry(Base):
    __tablename__ = "entry"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    brewery = Column(String(255), nullable=False)
    style = Column(String(100), nullable=True)
    volume = Column(Float, nullable=True)  # in ml
    datetime = Column(DateTime, nullable=False, default=func.now())
    bar = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)  # 0.0 – 5.0
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
