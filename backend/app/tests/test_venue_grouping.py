from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.schemas.entry import EntryCreate
from app.schemas.user import UserCreate
from app.services import entry as entry_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _dt(days_ago: int = 0, hour: int = 20) -> datetime:
    base = datetime.now(UTC).replace(tzinfo=None, hour=hour, minute=0, second=0, microsecond=0)
    return base - timedelta(days=days_ago)


def _bar(db: Session, name: str = "Le Comptoir", osm_id: int = 1) -> Bar:
    bar = Bar(osm_id=osm_id, osm_type="node", name=name, amenity="bar", latitude=48.85, longitude=2.35)
    db.add(bar)
    db.commit()
    db.refresh(bar)
    return bar


def _entry(bar_id: int, days_ago: int = 0, hour: int = 20, **kwargs) -> EntryCreate:
    return EntryCreate(type="IPA", volume=50.0, drink_datetime=_dt(days_ago, hour), bar_id=bar_id, **kwargs)


class TestVenueGrouping(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))
        self.comptoir = _bar(self.db, name="Le Comptoir", osm_id=1)
        self.relais = _bar(self.db, name="Le Relais", osm_id=2)

    def _create(self, *entries: EntryCreate) -> list:
        return [entry_service.create_entry(self.db, e, user_id=self.user.id) for e in entries]

    def _venues(self):
        return entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=self.user.id)

    # --- basic grouping ---

    def test_empty_entries_returns_empty(self) -> None:
        self.assertEqual(self._venues(), ())

    def test_single_entry_is_one_venue_with_bar_name(self) -> None:
        self._create(_entry(self.comptoir.id))
        venues = self._venues()
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].bar, "Le Comptoir")
        self.assertEqual(len(venues[0].entries), 1)

    # --- same day, same bar → grouped ---

    def test_same_day_same_bar_grouped_into_one_venue(self) -> None:
        self._create(_entry(self.comptoir.id, hour=19), _entry(self.comptoir.id, hour=21))
        venues = self._venues()
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].bar, "Le Comptoir")
        self.assertEqual(len(venues[0].entries), 2)

    def test_entries_within_venue_ordered_chronologically(self) -> None:
        self._create(_entry(self.comptoir.id, hour=21), _entry(self.comptoir.id, hour=19))
        venues = self._venues()
        times = [e.drink_datetime for e in venues[0].entries]
        self.assertEqual(times, sorted(times))

    # --- same day, different bars → separate venues ---

    def test_same_day_different_bars_are_separate_venues(self) -> None:
        self._create(_entry(self.comptoir.id), _entry(self.relais.id))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        bars = {v.bar for v in venues}
        self.assertEqual(bars, {"Le Comptoir", "Le Relais"})

    def test_distinct_bars_sharing_a_name_are_separate_venues(self) -> None:
        homonym = _bar(self.db, name="Le Comptoir", osm_id=3)
        self._create(_entry(self.comptoir.id), _entry(homonym.id))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        for v in venues:
            self.assertEqual(v.bar, "Le Comptoir")
            self.assertEqual(len(v.entries), 1)

    # --- different days, same bar → separate venues ---

    def test_different_days_same_bar_are_separate_venues(self) -> None:
        self._create(_entry(self.comptoir.id, days_ago=0), _entry(self.comptoir.id, days_ago=1))
        venues = self._venues()
        self.assertEqual(len(venues), 2)
        dates = [v.date for v in venues]
        self.assertEqual(dates, sorted(dates, reverse=True))

    # --- venue ordering ---

    def test_venues_ordered_by_date_descending(self) -> None:
        for days_ago in [2, 0, 1]:
            self._create(_entry(self.comptoir.id, days_ago=days_ago))
        venues = self._venues()
        dates = [v.date for v in venues]
        self.assertEqual(dates, sorted(dates, reverse=True))

    # --- mixed scenario ---

    def test_mixed_scenario(self) -> None:
        # today: 2 at Le Comptoir, 1 at Le Relais — yesterday: 1 at Le Comptoir
        self._create(
            _entry(self.comptoir.id, days_ago=0, hour=18),
            _entry(self.comptoir.id, days_ago=0, hour=20),
            _entry(self.relais.id, days_ago=0, hour=22),
            _entry(self.comptoir.id, days_ago=1, hour=20),
        )
        venues = self._venues()
        # Expected venues: today/Comptoir, today/Relais, yesterday/Comptoir = 3
        self.assertEqual(len(venues), 3)
        today_comptoir = next(
            v for v in venues if v.bar == "Le Comptoir" and v.entries[0].drink_datetime.date() == _dt(0).date()
        )
        self.assertEqual(len(today_comptoir.entries), 2)
