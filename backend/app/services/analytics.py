from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.schemas.entry import StatsSummary


def get_stats_summary(db: Session, user_id: int) -> StatsSummary:
    now = datetime.now(UTC).replace(tzinfo=None)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    all_entries: list[Entry] = db.query(Entry).filter(Entry.user_id == user_id).all()

    weekly_count = sum(1 for e in all_entries if e.drink_datetime >= week_ago)
    monthly_count = sum(1 for e in all_entries if e.drink_datetime >= month_ago)

    top_types = [t for t, _ in Counter(e.type for e in all_entries if e.type).most_common(3)]
    top_names = [n for n, _ in Counter(e.name for e in all_entries if e.name).most_common(3)]

    total_liters = round(sum(e.volume for e in all_entries) / 1000, 2)

    return StatsSummary(
        weekly_count=weekly_count,
        monthly_count=monthly_count,
        top_types=top_types,
        top_names=top_names,
        total_liters=total_liters,
    )
