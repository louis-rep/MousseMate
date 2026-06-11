from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class Entry(Base):
    __tablename__ = "entry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    volume: Mapped[float] = mapped_column(nullable=False)
    drink_datetime: Mapped[datetime] = mapped_column(nullable=False, default=func.now())
    bar_id: Mapped[int] = mapped_column(ForeignKey("bar.id"), nullable=False, index=True)
    rating: Mapped[float | None] = mapped_column(nullable=True)  # 0.0 – 5.0
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
