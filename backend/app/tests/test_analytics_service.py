from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.schemas.entry import EntryCreate
from app.services import analytics, entry as entry_service
from app.tests.base import BaseTestDatabase


def _entry(days_ago: int = 0, type: str = "IPA", name: str | None = None) -> EntryCreate:
    return EntryCreate(
        type=type,
        name=name,
        volume=50.0,
        drink_datetime=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_ago),
    )


class TestWeeklyAndMonthlyCounts(BaseTestDatabase):
    def test_counts_entries_in_last_7_days(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0))
        entry_service.create_entry(self.db, _entry(days_ago=6))
        entry_service.create_entry(self.db, _entry(days_ago=8))  # outside window
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.weekly_count, 2)

    def test_counts_entries_in_last_30_days(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0))
        entry_service.create_entry(self.db, _entry(days_ago=29))
        entry_service.create_entry(self.db, _entry(days_ago=31))  # outside window
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.monthly_count, 2)

    def test_empty_db_returns_zeros(self) -> None:
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.weekly_count, 0)
        self.assertEqual(stats.monthly_count, 0)


class TestTopTypes(BaseTestDatabase):
    def test_returns_most_frequent_types(self) -> None:
        for _ in range(3):
            entry_service.create_entry(self.db, _entry(type="IPA"))
        for _ in range(2):
            entry_service.create_entry(self.db, _entry(type="Stout"))
        entry_service.create_entry(self.db, _entry(type="Lager"))
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.top_types[0], "IPA")
        self.assertIn("Stout", stats.top_types)

    def test_returns_at_most_3_types(self) -> None:
        for t in ["IPA", "Stout", "Lager", "Wheat", "Sour"]:
            entry_service.create_entry(self.db, _entry(type=t))
        stats = analytics.get_stats_summary(self.db)
        self.assertLessEqual(len(stats.top_types), 3)


class TestTopNames(BaseTestDatabase):
    def test_returns_most_frequent_names(self) -> None:
        for _ in range(3):
            entry_service.create_entry(self.db, _entry(name="Heineken"))
        entry_service.create_entry(self.db, _entry(name="Leffe"))
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.top_names[0], "Heineken")

    def test_ignores_entries_with_no_name(self) -> None:
        entry_service.create_entry(self.db, _entry(name=None))
        entry_service.create_entry(self.db, _entry(name=None))
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.top_names, [])


class TestStreak(BaseTestDatabase):
    def test_consecutive_days_streak(self) -> None:
        for days_ago in [0, 1, 2]:
            entry_service.create_entry(self.db, _entry(days_ago=days_ago))
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.current_streak_days, 3)

    def test_streak_breaks_on_gap(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0))
        entry_service.create_entry(self.db, _entry(days_ago=2))  # gap on day 1
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.current_streak_days, 1)

    def test_no_entry_today_gives_zero_streak(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=1))
        stats = analytics.get_stats_summary(self.db)
        self.assertEqual(stats.current_streak_days, 0)
