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


class TestTotalLiters(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_sums_all_volumes_in_liters(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0), user_id=self.user.id)   # 50 mL
        entry_service.create_entry(self.db, _entry(days_ago=40), user_id=self.user.id)  # 50 mL — outside weekly/monthly but still total
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertAlmostEqual(stats.total_liters, 0.1, places=3)

    def test_empty_db_returns_zero(self) -> None:
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.total_liters, 0.0)


class TestDailyLiters(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_no_entries_returns_no_series(self) -> None:
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(len(stats.daily_liters), 0)

    def test_each_series_has_7_days(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0, type="IPA"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(len(stats.daily_liters[0].daily), 7)

    def test_days_are_chronological(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0, type="IPA"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        dates = [d.date for d in stats.daily_liters[0].daily]
        self.assertEqual(dates, sorted(dates))

    def test_volume_appears_on_correct_day_and_type(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0, type="IPA"), user_id=self.user.id)  # 50 mL
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        ipa_series = next(s for s in stats.daily_liters if s.type == "IPA")
        self.assertAlmostEqual(ipa_series.daily[-1].liters, 0.05, places=3)

    def test_entries_outside_window_not_included(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=8, type="IPA"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(len(stats.daily_liters), 0)

    def test_one_series_per_type(self) -> None:
        entry_service.create_entry(self.db, _entry(days_ago=0, type="IPA"), user_id=self.user.id)
        entry_service.create_entry(self.db, _entry(days_ago=0, type="Stout"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        types = {s.type for s in stats.daily_liters}
        self.assertEqual(types, {"IPA", "Stout"})


class TestLitersByType(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def _entry_bar(self, type: str, bar: str | None = None, days_ago: int = 0) -> EntryCreate:
        dt = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_ago)
        return EntryCreate(type=type, volume=50.0, drink_datetime=dt, bar=bar)

    def test_one_series_per_bar(self) -> None:
        entry_service.create_entry(self.db, self._entry_bar("IPA", bar="Bar A"), user_id=self.user.id)
        entry_service.create_entry(self.db, self._entry_bar("IPA", bar="Bar B"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        bars = {s.bar for s in stats.liters_by_type}
        self.assertEqual(bars, {"Bar A", "Bar B"})

    def test_groups_volume_by_type_within_bar(self) -> None:
        entry_service.create_entry(self.db, self._entry_bar("IPA", bar="Bar A"), user_id=self.user.id)
        entry_service.create_entry(self.db, self._entry_bar("IPA", bar="Bar A"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        bar_a = next(s for s in stats.liters_by_type if s.bar == "Bar A")
        ipa = next(v for v in bar_a.values if v.type == "IPA")
        self.assertAlmostEqual(ipa.liters, 0.1, places=3)

    def test_values_sorted_by_liters_descending(self) -> None:
        entry_service.create_entry(self.db, self._entry_bar("Stout", bar="Bar A"), user_id=self.user.id)
        for _ in range(3):
            entry_service.create_entry(self.db, self._entry_bar("IPA", bar="Bar A"), user_id=self.user.id)
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        bar_a = next(s for s in stats.liters_by_type if s.bar == "Bar A")
        self.assertEqual(bar_a.values[0].type, "IPA")
