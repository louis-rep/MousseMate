from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.models.entry import Entry
from app.schemas.entry import BarTypeLiters, DailyLiters, StatsSummary, TypeDailyLiters, TypeLiters


def get_stats_summary(db: Session, user_id: int) -> StatsSummary:
    now = datetime.now(UTC).replace(tzinfo=None)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    rows: list[tuple[Entry, str]] = (
        db.query(Entry, Bar.name).join(Bar, Entry.bar_id == Bar.id).filter(Entry.user_id == user_id).all()
    )
    all_entries = [e for e, _ in rows]

    weekly_count = sum(1 for e in all_entries if e.drink_datetime >= week_ago)
    monthly_count = sum(1 for e in all_entries if e.drink_datetime >= month_ago)

    top_types = [t for t, _ in Counter(e.type for e in all_entries if e.type).most_common(3)]
    top_names = [n for n, _ in Counter(e.name for e in all_entries if e.name).most_common(3)]

    total_liters = round(sum(e.volume for e in all_entries) / 1000, 2)

    week_dates = [now.date() - timedelta(days=i) for i in range(6, -1, -1)]
    type_daily_volumes: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for e in all_entries:
        if e.drink_datetime >= week_ago and e.type:
            type_daily_volumes[e.type][e.drink_datetime.date()] += e.volume
    daily_liters = tuple(
        TypeDailyLiters(
            type=t,
            daily=tuple(DailyLiters(date=d, liters=round(vols.get(d, 0) / 1000, 3)) for d in week_dates),
        )
        for t, vols in sorted(type_daily_volumes.items())
    )

    bar_type_volumes: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for e, bar_name in rows:
        if e.type:
            bar_type_volumes[bar_name][e.type] += e.volume
    liters_by_type = tuple(
        BarTypeLiters(
            bar=bar,
            values=tuple(
                TypeLiters(type=t, liters=round(v / 1000, 3)) for t, v in sorted(vols.items(), key=lambda x: -x[1])
            ),
        )
        for bar, vols in sorted(bar_type_volumes.items())
    )

    return StatsSummary(
        weekly_count=weekly_count,
        monthly_count=monthly_count,
        top_types=top_types,
        top_names=top_names,
        total_liters=total_liters,
        daily_liters=daily_liters,
        liters_by_type=liters_by_type,
    )
