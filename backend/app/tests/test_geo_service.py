from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.schemas.entry import EntryCreate
from app.schemas.user import UserCreate
from app.services import entry as entry_service
from app.services import follow as follow_service
from app.services import geo as geo_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _dt(days_ago: int = 0, hour: int = 20) -> datetime:
    base = datetime.now(UTC).replace(tzinfo=None, hour=hour, minute=0, second=0, microsecond=0)
    return base - timedelta(days=days_ago)


def _bar(db: Session, name: str = "Le Comptoir", osm_id: int = 1, **kwargs) -> Bar:
    defaults = {"osm_type": "node", "amenity": "bar", "latitude": 48.85, "longitude": 2.35}
    bar = Bar(osm_id=osm_id, name=name, **{**defaults, **kwargs})
    db.add(bar)
    db.commit()
    db.refresh(bar)
    return bar


def _entry(bar_id: int, volume: float = 500.0, days_ago: int = 0, hour: int = 20) -> EntryCreate:
    return EntryCreate(type="IPA", volume=volume, drink_datetime=_dt(days_ago, hour), bar_id=bar_id)


class TestGeoService(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.louis = user_service.create_user(self.db, UserCreate(username="louis", password="pass"))
        self.mate = user_service.create_user(self.db, UserCreate(username="marco", password="pass"))
        self.stranger = user_service.create_user(self.db, UserCreate(username="stranger", password="pass"))
        follow_service.follow_user(self.db, self.louis.id, self.mate.id)
        self.comptoir = _bar(self.db, name="Le Comptoir", osm_id=1)
        self.relais = _bar(self.db, name="Le Relais", osm_id=2)

    def _create(self, user_id: int, *entries: EntryCreate) -> None:
        for e in entries:
            entry_service.create_entry(self.db, e, user_id=user_id)

    def _venue(self, response, bar_id: int):
        return next(v for v in response.venues if v.bar_id == bar_id)

    # --- empty / scope ---

    def test_no_entries_returns_empty_venues(self) -> None:
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="me")
        self.assertEqual(response.scope, "me")
        self.assertEqual(response.venues, ())

    def test_scope_me_excludes_mate_entries(self) -> None:
        self._create(self.louis.id, _entry(self.comptoir.id))
        self._create(self.mate.id, _entry(self.relais.id))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="me")
        self.assertEqual([v.bar_id for v in response.venues], [self.comptoir.id])

    def test_scope_mates_includes_self_and_mates_but_not_strangers(self) -> None:
        self._create(self.louis.id, _entry(self.comptoir.id))
        self._create(self.mate.id, _entry(self.comptoir.id))
        self._create(self.stranger.id, _entry(self.relais.id))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="mates")
        self.assertEqual([v.bar_id for v in response.venues], [self.comptoir.id])
        drinkers = {d.username for d in response.venues[0].drinkers}
        self.assertEqual(drinkers, {"louis", "marco"})

    # --- aggregation ---

    def test_venue_totals_and_last_visit(self) -> None:
        self._create(self.louis.id, _entry(self.comptoir.id, volume=500, days_ago=2))
        self._create(self.mate.id, _entry(self.comptoir.id, volume=250, days_ago=1))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="mates")
        venue = self._venue(response, self.comptoir.id)
        self.assertEqual(venue.entry_count, 2)
        self.assertAlmostEqual(venue.total_liters, 0.75)
        self.assertEqual(venue.last_visit, _dt(days_ago=1))
        self.assertEqual(venue.name, "Le Comptoir")
        self.assertEqual(venue.latitude, 48.85)

    def test_drinkers_per_user_liters_sorted_desc(self) -> None:
        self._create(self.louis.id, _entry(self.comptoir.id, volume=250), _entry(self.comptoir.id, volume=250))
        self._create(self.mate.id, _entry(self.comptoir.id, volume=1000))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="mates")
        drinkers = self._venue(response, self.comptoir.id).drinkers
        self.assertEqual([d.username for d in drinkers], ["marco", "louis"])
        self.assertEqual([d.liters for d in drinkers], [1.0, 0.5])
        self.assertEqual([d.entry_count for d in drinkers], [1, 2])

    def test_bars_without_entries_are_absent(self) -> None:
        self._create(self.louis.id, _entry(self.comptoir.id))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="me")
        self.assertEqual([v.bar_id for v in response.venues], [self.comptoir.id])

    # --- edge cases ---

    def test_manual_placeholder_bar_is_excluded(self) -> None:
        unknown = _bar(self.db, name="Unknown bar", osm_id=0, osm_type="manual")
        self._create(self.louis.id, _entry(unknown.id), _entry(self.comptoir.id))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="me")
        self.assertEqual([v.bar_id for v in response.venues], [self.comptoir.id])

    def test_closed_bar_with_entries_still_appears_flagged(self) -> None:
        closed = _bar(self.db, name="Le Disparu", osm_id=3, is_closed=True)
        self._create(self.louis.id, _entry(closed.id))
        response = geo_service.get_venue_map(self.db, self.louis.id, scope="me")
        venue = self._venue(response, closed.id)
        self.assertTrue(venue.is_closed)

    def test_null_address_and_postcode_survive(self) -> None:
        self._create(self.louis.id, _entry(self.comptoir.id))
        venue = geo_service.get_venue_map(self.db, self.louis.id, scope="me").venues[0]
        self.assertIsNone(venue.address)
        self.assertIsNone(venue.postcode)


class TestPostcodeToArrondissement(unittest.TestCase):
    def test_mapping(self) -> None:
        cases = {
            "75001": 1,
            "75011": 11,
            "75020": 20,
            "75116": 16,  # Passy, part of the 16th
            "75000": None,
            "75021": None,
            "92100": None,
            "7501": None,
            "750ab": None,
            None: None,
        }
        for postcode, expected in cases.items():
            self.assertEqual(geo_service._postcode_to_arrondissement(postcode), expected, msg=f"postcode={postcode}")


class TestArrondissementMap(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.louis = user_service.create_user(self.db, UserCreate(username="louis", password="pass"))
        self.mate = user_service.create_user(self.db, UserCreate(username="marco", password="pass"))
        follow_service.follow_user(self.db, self.louis.id, self.mate.id)
        self.onzieme = _bar(self.db, name="Bar du 11e", osm_id=1, postcode="75011")
        self.onzieme_bis = _bar(self.db, name="Autre bar du 11e", osm_id=2, postcode="75011")
        self.passy = _bar(self.db, name="Bar de Passy", osm_id=3, postcode="75116")

    def _create(self, user_id: int, *entries: EntryCreate) -> None:
        for e in entries:
            entry_service.create_entry(self.db, e, user_id=user_id)

    def test_no_entries_returns_empty(self) -> None:
        response = geo_service.get_arrondissement_map(self.db, self.louis.id, scope="me")
        self.assertEqual(response.scope, "me")
        self.assertEqual(response.arrondissements, ())

    def test_aggregates_across_bars_of_same_arrondissement(self) -> None:
        self._create(self.louis.id, _entry(self.onzieme.id, volume=500), _entry(self.onzieme_bis.id, volume=250))
        response = geo_service.get_arrondissement_map(self.db, self.louis.id, scope="me")
        self.assertEqual(len(response.arrondissements), 1)
        stat = response.arrondissements[0]
        self.assertEqual(stat.arrondissement, 11)
        self.assertEqual(stat.entry_count, 2)
        self.assertAlmostEqual(stat.total_liters, 0.75)

    def test_passy_postcode_counts_in_the_16th(self) -> None:
        self._create(self.louis.id, _entry(self.passy.id, volume=500))
        response = geo_service.get_arrondissement_map(self.db, self.louis.id, scope="me")
        self.assertEqual([s.arrondissement for s in response.arrondissements], [16])

    def test_unmappable_postcodes_are_excluded(self) -> None:
        no_postcode = _bar(self.db, name="Sans code postal", osm_id=4)
        suburb = _bar(self.db, name="Banlieue", osm_id=5, postcode="92100")
        self._create(self.louis.id, _entry(no_postcode.id), _entry(suburb.id), _entry(self.onzieme.id))
        response = geo_service.get_arrondissement_map(self.db, self.louis.id, scope="me")
        self.assertEqual([s.arrondissement for s in response.arrondissements], [11])

    def test_scope_mates_includes_mate_entries(self) -> None:
        self._create(self.louis.id, _entry(self.onzieme.id, volume=500))
        self._create(self.mate.id, _entry(self.passy.id, volume=1000))
        me = geo_service.get_arrondissement_map(self.db, self.louis.id, scope="me")
        mates = geo_service.get_arrondissement_map(self.db, self.louis.id, scope="mates")
        self.assertEqual([s.arrondissement for s in me.arrondissements], [11])
        self.assertEqual({s.arrondissement for s in mates.arrondissements}, {11, 16})
