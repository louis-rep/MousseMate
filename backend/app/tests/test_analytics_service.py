from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.schemas.entry import EntryCreate
from app.schemas.user import UserCreate
from app.services import analytics
from app.services import entry as entry_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _bar(db: Session, name: str = "Le Comptoir", osm_id: int = 1) -> Bar:
    bar = Bar(osm_id=osm_id, osm_type="node", name=name, amenity="bar", latitude=48.85, longitude=2.35)
    db.add(bar)
    db.commit()
    db.refresh(bar)
    return bar


def _entry(bar_id: int, days_ago: int = 0, type: str = "IPA", name: str | None = None) -> EntryCreate:
    return EntryCreate(
        type=type,
        name=name,
        volume=50.0,
        drink_datetime=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_ago),
        bar_id=bar_id,
    )


class AnalyticsTestBase(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))
        self.bar = _bar(self.db)

    def _create(self, *entries: EntryCreate) -> None:
        for e in entries:
            entry_service.create_entry(self.db, e, user_id=self.user.id)


class TestWeeklyAndMonthlyCounts(AnalyticsTestBase):
    def test_counts_entries_in_last_7_days(self) -> None:
        self._create(_entry(self.bar.id, days_ago=0), _entry(self.bar.id, days_ago=6))
        self._create(_entry(self.bar.id, days_ago=8))  # outside window
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.weekly_count, 2)

    def test_counts_entries_in_last_30_days(self) -> None:
        self._create(_entry(self.bar.id, days_ago=0), _entry(self.bar.id, days_ago=29))
        self._create(_entry(self.bar.id, days_ago=31))  # outside window
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.monthly_count, 2)

    def test_empty_db_returns_zeros(self) -> None:
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.weekly_count, 0)
        self.assertEqual(stats.monthly_count, 0)


class TestTopTypes(AnalyticsTestBase):
    def test_returns_most_frequent_types(self) -> None:
        self._create(*[_entry(self.bar.id, type="IPA") for _ in range(3)])
        self._create(*[_entry(self.bar.id, type="Stout") for _ in range(2)])
        self._create(_entry(self.bar.id, type="Lager"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.top_types[0], "IPA")
        self.assertIn("Stout", stats.top_types)

    def test_returns_at_most_3_types(self) -> None:
        self._create(*[_entry(self.bar.id, type=t) for t in ["IPA", "Stout", "Lager", "Wheat", "Sour"]])
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertLessEqual(len(stats.top_types), 3)


class TestTopNames(AnalyticsTestBase):
    def test_returns_most_frequent_names(self) -> None:
        self._create(*[_entry(self.bar.id, name="Heineken") for _ in range(3)])
        self._create(_entry(self.bar.id, name="Leffe"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.top_names[0], "Heineken")

    def test_ignores_entries_with_no_name(self) -> None:
        self._create(_entry(self.bar.id, name=None), _entry(self.bar.id, name=None))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.top_names, [])


class TestTotalLiters(AnalyticsTestBase):
    def test_sums_all_volumes_in_liters(self) -> None:
        # 50 mL each; the second is outside weekly/monthly windows but still in total
        self._create(_entry(self.bar.id, days_ago=0), _entry(self.bar.id, days_ago=40))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertAlmostEqual(stats.total_liters, 0.1, places=3)

    def test_empty_db_returns_zero(self) -> None:
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(stats.total_liters, 0.0)


class TestDailyLiters(AnalyticsTestBase):
    def test_no_entries_returns_no_series(self) -> None:
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(len(stats.daily_liters), 0)

    def test_each_series_has_7_days(self) -> None:
        self._create(_entry(self.bar.id, days_ago=0, type="IPA"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(len(stats.daily_liters[0].daily), 7)

    def test_days_are_chronological(self) -> None:
        self._create(_entry(self.bar.id, days_ago=0, type="IPA"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        dates = [d.date for d in stats.daily_liters[0].daily]
        self.assertEqual(dates, sorted(dates))

    def test_volume_appears_on_correct_day_and_type(self) -> None:
        self._create(_entry(self.bar.id, days_ago=0, type="IPA"))  # 50 mL
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        ipa_series = next(s for s in stats.daily_liters if s.type == "IPA")
        self.assertAlmostEqual(ipa_series.daily[-1].liters, 0.05, places=3)

    def test_entries_outside_window_not_included(self) -> None:
        self._create(_entry(self.bar.id, days_ago=8, type="IPA"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        self.assertEqual(len(stats.daily_liters), 0)

    def test_one_series_per_type(self) -> None:
        self._create(_entry(self.bar.id, days_ago=0, type="IPA"), _entry(self.bar.id, days_ago=0, type="Stout"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        types = {s.type for s in stats.daily_liters}
        self.assertEqual(types, {"IPA", "Stout"})


class TestLitersByType(AnalyticsTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.bar_a = _bar(self.db, name="Bar A", osm_id=2)
        self.bar_b = _bar(self.db, name="Bar B", osm_id=3)

    def test_one_series_per_bar(self) -> None:
        self._create(_entry(self.bar_a.id, type="IPA"), _entry(self.bar_b.id, type="IPA"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        bars = {s.bar for s in stats.liters_by_type}
        self.assertEqual(bars, {"Bar A", "Bar B"})

    def test_groups_volume_by_type_within_bar(self) -> None:
        self._create(_entry(self.bar_a.id, type="IPA"), _entry(self.bar_a.id, type="IPA"))
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        bar_a = next(s for s in stats.liters_by_type if s.bar == "Bar A")
        ipa = next(v for v in bar_a.values if v.type == "IPA")
        self.assertAlmostEqual(ipa.liters, 0.1, places=3)

    def test_values_sorted_by_liters_descending(self) -> None:
        self._create(_entry(self.bar_a.id, type="Stout"))
        self._create(*[_entry(self.bar_a.id, type="IPA") for _ in range(3)])
        stats = analytics.get_stats_summary(self.db, user_id=self.user.id)
        bar_a = next(s for s in stats.liters_by_type if s.bar == "Bar A")
        self.assertEqual(bar_a.values[0].type, "IPA")
