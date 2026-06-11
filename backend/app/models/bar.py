from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class Bar(Base):
    """OSM-sourced venue referential. Rows are never deleted: bars that disappear
    from OSM are flagged is_closed so entries can keep referencing them."""

    __tablename__ = "bar"
    __table_args__ = (UniqueConstraint("osm_type", "osm_id", name="uq_bar_osm_type_osm_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    osm_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    osm_type: Mapped[str] = mapped_column(String(10), nullable=False)  # node / way / relation
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amenity: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # TODO(scale): city becomes a real dimension when the referential goes France/global
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Paris", index=True)
    is_closed: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
