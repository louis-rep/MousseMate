from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.schemas.entry import EntryCreate
from app.schemas.user import UserCreate
from app.services import entry as entry_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _dt(days_ago: int = 0, hour: int = 20) -> datetime:
    base = datetime.now(UTC).replace(tzinfo=None, hour=hour, minute=0, second=0, microsecond=0)
    return base - timedelta(days=days_ago)


def _entry(bar: str | None = "Le Comptoir", days_ago: int = 0, hour: int = 20, **kwargs) -> EntryCreate:
    return EntryCreate(type="IPA", volume=50.0, drink_datetime=_dt(days_ago, hour), bar=bar, **kwargs)


class TestVenueGrouping(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def _create(self, *entries: EntryCreate) -> list:
        return [entry_service.create_entry(self.db, e, user_id=self.user.id) for e in entries]

    def _venues(self):
        return entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=self.user.id)

    # --- basic grouping ---

    def test_empty_entries_returns_empty(self) -> None:
        self.assertEqual(self._venues(), ())

    def test_single_entry_with_bar_is_one_venue(self) -> None:
        self._create(_entry(bar="Le Comptoir"))
        venues = self._venues()
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].bar, "Le Comptoir")
        self.assertEqual(len(venues[0].entries), 1)

    def test_single_entry_no_bar_is_one_venue(self) -> None:
        self._create(_entry(bar=None))
        venues = self._venues()
        self.assertEqual(len(venues), 1)
        self.assertIsNone(venues[0].bar)
        self.assertEqual(len(venues[0].entries), 1)

    # --- same day, same bar → grouped ---

    def test_same_day_same_bar_grouped_into_one_venue(self) -> None:
        self._create(_entry(bar="Le Comptoir", hour=19), _entry(bar="Le Comptoir", hour=21))
        venues = self._venues()
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].bar, "Le Comptoir")
        self.assertEqual(len(venues[0].entries), 2)

    def test_entries_within_venue_ordered_chronologically(self) -> None:
        self._create(_entry(bar="Le Comptoir", hour=21), _entry(bar="Le Comptoir", hour=19))
        venues = self._venues()
        times = [e.drink_datetime for e in venues[0].entries]
        self.assertEqual(times, sorted(times))

    # --- same day, different bars → separate venues ---

    def test_same_day_different_bars_are_separate_venues(self) -> None:
        self._create(_entry(bar="Le Comptoir"), _entry(bar="Le Relais"))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        bars = {v.bar for v in venues}
        self.assertEqual(bars, {"Le Comptoir", "Le Relais"})

    # --- different days, same bar → separate venues ---

    def test_different_days_same_bar_are_separate_venues(self) -> None:
        self._create(_entry(bar="Le Comptoir", days_ago=0), _entry(bar="Le Comptoir", days_ago=1))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        dates = [v.date for v in venues]
        self.assertEqual(dates, sorted(dates, reverse=True))

    # --- NaN bar logic ---

    def test_two_entries_no_bar_same_day_are_separate_venues(self) -> None:
        self._create(_entry(bar=None, hour=19), _entry(bar=None, hour=21))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        for v in venues:
            self.assertIsNone(v.bar)
            self.assertEqual(len(v.entries), 1)

    def test_no_bar_entry_not_grouped_with_bar_entry_same_day(self) -> None:
        self._create(_entry(bar="Le Comptoir"), _entry(bar=None))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        bars = {v.bar for v in venues}
        self.assertEqual(bars, {"Le Comptoir", None})

    # --- venue ordering ---

    def test_venues_ordered_by_date_descending(self) -> None:
        for days_ago in [2, 0, 1]:
            self._create(_entry(bar="Le Comptoir", days_ago=days_ago))
        venues = self._venues()
        dates = [v.date for v in venues]
        self.assertEqual(dates, sorted(dates, reverse=True))

    # --- mixed scenario ---

    def test_mixed_scenario(self) -> None:
        # today: 2 at Le Comptoir, 1 at Le Relais, 1 no bar
        # yesterday: 1 at Le Comptoir, 1 no bar
        self._create(
            _entry(bar="Le Comptoir", days_ago=0, hour=18),
            _entry(bar="Le Comptoir", days_ago=0, hour=20),
            _entry(bar="Le Relais", days_ago=0, hour=22),
            _entry(bar=None, days_ago=0, hour=23),
            _entry(bar="Le Comptoir", days_ago=1, hour=20),
            _entry(bar=None, days_ago=1, hour=21),
        )
        venues = self._venues()
        # Expected venues: today/Comptoir, today/Relais, today/None, yesterday/Comptoir, yesterday/None = 5
        self.assertEqual(len(venues), 5)
        today_comptoir = next(v for v in venues if v.bar == "Le Comptoir" and v.entries[0].drink_datetime.date() == _dt(0).date())
        self.assertEqual(len(today_comptoir.entries), 2)
