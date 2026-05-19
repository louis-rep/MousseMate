from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.checkin import CheckIn
from app.schemas.checkin import CheckInCreate, CheckInUpdate


def get_checkin(db: Session, checkin_id: int) -> Optional[CheckIn]:
    """Return a single CheckIn by primary key, or None."""
    return db.query(CheckIn).filter(CheckIn.id == checkin_id).first()


def list_checkins(db: Session, skip: int = 0, limit: int = 20) -> list[CheckIn]:
    """Return a paginated list of check-ins ordered by most recent first."""
    return (
        db.query(CheckIn)
        .order_by(CheckIn.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_checkin(db: Session, data: CheckInCreate) -> CheckIn:
    """Persist a new check-in and return it."""
    checkin = CheckIn(**data.model_dump())
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def update_checkin(
    db: Session, checkin_id: int, data: CheckInUpdate
) -> Optional[CheckIn]:
    """Apply a partial update to an existing check-in. Returns None if not found."""
    checkin = get_checkin(db, checkin_id)
    if checkin is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(checkin, field, value)

    db.commit()
    db.refresh(checkin)
    return checkin


def delete_checkin(db: Session, checkin_id: int) -> bool:
    """Delete a check-in. Returns True if deleted, False if not found."""
    checkin = get_checkin(db, checkin_id)
    if checkin is None:
        return False
    db.delete(checkin)
    db.commit()
    return True


def get_stats_summary(db: Session) -> dict:
    """
    Compute aggregated stats:
    - weekly_count: check-ins in the last 7 days
    - monthly_count: check-ins in the last 30 days
    - top_styles: top 3 non-null styles by frequency
    - top_breweries: top 3 non-null breweries by frequency
    - current_streak_days: consecutive calendar days ending today with ≥1 check-in
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    all_checkins: list[CheckIn] = db.query(CheckIn).all()

    weekly_count = sum(1 for c in all_checkins if c.created_at >= week_ago)
    monthly_count = sum(1 for c in all_checkins if c.created_at >= month_ago)

    # Top styles
    styles = [c.style for c in all_checkins if c.style]
    top_styles = [style for style, _ in Counter(styles).most_common(3)]

    # Top breweries
    breweries = [c.brewery for c in all_checkins if c.brewery]
    top_breweries = [brewery for brewery, _ in Counter(breweries).most_common(3)]

    # Current streak — consecutive days ending today
    checkin_dates: set[date] = {c.created_at.date() for c in all_checkins}
    streak = 0
    current_day = now.date()
    while current_day in checkin_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return {
        "weekly_count": weekly_count,
        "monthly_count": monthly_count,
        "top_styles": top_styles,
        "top_breweries": top_breweries,
        "current_streak_days": streak,
    }
