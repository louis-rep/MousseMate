from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class UserEntryLike(Base):
    __tablename__ = "user_entry_like"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entry.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
