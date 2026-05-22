from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.schemas.entry import EntryCreate
from app.schemas.user import UserCreate
from app.services import analytics
from app.services import entry as entry_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _entry(days_ago: int = 0, type: str = "IPA", name: str | None = None) -> EntryCreate:
    return EntryCreate(
        type=type,
        name=name,
        volume=50.0,
        drink_datetime=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_ago),
    )


class TestWeeklyAndMonthlyCounts(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_counts_entries_in_last_7_days(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(days_ago=6), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(days_ago=8), user_id=self.user.id)  # outside window
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.weekly_count, 2)

    def test_counts_entries_in_last_30_days(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(days_ago=29), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(days_ago=31), user_id=self.user.id)  # outside window
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.monthly_count, 2)

    def test_empty_db_returns_zeros(self) -> None:
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.weekly_count, 0)
        self.assertEqual(stats.monthly_count, 0)


class TestTopTypes(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_returns_most_frequent_types(self) -> None:
        for _ in range(3):
            entry_service.create_entry(self.db, _entry(type="IPA"), user_id=self.user.id)
        for _ in range(2):
            entry_service.create_entry(self.db, _entry(type="Stout"), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(type="Lager"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.top_types[0], "IPA")
        self.assertIn("Stout", stats.top_types)

    def test_returns_at_most_3_types(self) -> None:
        for t in ["IPA", "Stout", "Lager", "Wheat", "Sour"]:
            entry_service.create_entry(self.db, _entry(type=t), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertLessEqual(len(stats.top_types), 3)


class TestTopNames(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_returns_most_frequent_names(self) -> None:
        for _ in range(3):
            entry_service.create_entry(self.db, _entry(name="Heineken"), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(name="Leffe"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.top_names[0], "Heineken")

    def test_ignores_entries_with_no_name(self) -> None:
        entry_service.create_entry(self.db, _entry(name=None), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(name=None), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.top_names, [])


class TestStreak(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_consecutive_days_streak(self) -> None:
        for days_ago in [0, 1, 2]:
            entry_service.create_entry(self.db, _entry(days_ago=days_ago), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.current_streak_days, 3)

    def test_streak_breaks_on_gap(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(days_ago=2), user_id=self.user.id)  # gap on day 1
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.current_streak_days, 1)

    def test_no_entry_today_gives_zero_streak(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=1), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.current_streak_days, 0)
