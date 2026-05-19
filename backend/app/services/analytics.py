from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.schemas.entry import StatsSummary


def get_stats_summary(db: Session) -> StatsSummary:
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    all_entries: list[Entry] = db.query(Entry).all()

    weekly_count = sum(1 for e in all_entries if e.datetime >= week_ago)
    monthly_count = sum(1 for e in all_entries if e.datetime >= month_ago)

    top_styles = [s for s, _ in Counter(e.style for e in all_entries if e.style).most_common(3)]
    top_breweries = [b for b, _ in Counter(e.brewery for e in all_entries if e.brewery).most_common(3)]

    # Consecutive calendar days ending today with ≥1 entry
    entry_dates: set[date] = {e.datetime.date() for e in all_entries}
    streak = 0
    current_day = now.date()
    while current_day in entry_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return StatsSummary(
        weekly_count=weekly_count,
        monthly_count=monthly_count,
        top_styles=top_styles,
        top_breweries=top_breweries,
        current_streak_days=streak,
    )
