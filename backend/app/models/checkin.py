from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    beer_name = Column(String(255), nullable=False)
    brewery = Column(String(255), nullable=True)
    style = Column(String(100), nullable=True)
    rating = Column(Float, nullable=True)  # 0.0 – 5.0
    notes = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    venue = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
