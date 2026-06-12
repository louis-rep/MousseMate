from __future__ import annotations

from app.models.bar import Bar
from app.services import bar as bar_service
from app.tests.base import BaseTestDatabase


def _element(osm_id: int = 1, **overrides) -> dict:
    element = {
        "osm_id": osm_id,
        "osm_type": "node",
        "name": "Le Comptoir",
        "amenity": "bar",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "address": "5 Rue Mouffetard",
        "postcode": "75005",
        "city": "Paris",
    }
    element.update(overrides)
    return element


class TestSyncBars(BaseTestDatabase):
    def _get_bar(self, osm_id: int = 1) -> Bar:
        return self.db.query(Bar).filter(Bar.osm_id == osm_id, Bar.osm_type == "node").one()

    def test_inserts_new_bars(self) -> None:
        counts = bar_service.sync_bars(self.db, [_element(1), _element(2, name="Le Relais")])
        self.assertEqual(counts["inserted"], 2)
        self.assertEqual(self.db.query(Bar).count(), 2)

    def test_missing_postcode_is_derived_from_coordinates(self) -> None:
        # element() coords are Notre-Dame -> 4th arrondissement
        bar_service.sync_bars(self.db, [_element(postcode=None, latitude=48.8530, longitude=2.3499)])
        self.assertEqual(self._get_bar().postcode, "75004")

    def test_osm_postcode_wins_over_derivation(self) -> None:
        bar_service.sync_bars(self.db, [_element(postcode="75005", latitude=48.8530, longitude=2.3499)])
        self.assertEqual(self._get_bar().postcode, "75005")

    def test_existing_bar_without_postcode_is_backfilled_on_next_sync(self) -> None:
        self.db.add(
            Bar(
                osm_id=1,
                osm_type="node",
                name="Le Comptoir",
                amenity="bar",
                latitude=48.8530,
                longitude=2.3499,
                postcode=None,
            )
        )
        self.db.commit()
        counts = bar_service.sync_bars(self.db, [_element(postcode=None, latitude=48.8530, longitude=2.3499)])
        self.assertEqual(counts["updated"], 1)
        self.assertEqual(self._get_bar().postcode, "75004")

    def test_bar_outside_polygons_keeps_null_postcode(self) -> None:
        # La Défense — inside no arrondissement polygon
        bar_service.sync_bars(self.db, [_element(postcode=None, latitude=48.8924, longitude=2.2361)])
        self.assertIsNone(self._get_bar().postcode)

    def test_updates_changed_fields(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        counts = bar_service.sync_bars(self.db, [_element(name="Le Nouveau Comptoir", latitude=48.8567)])
        self.assertEqual(counts["updated"], 1)
        bar = self._get_bar()
        self.assertEqual(bar.name, "Le Nouveau Comptoir")
        self.assertEqual(bar.latitude, 48.8567)

    def test_unchanged_bar_is_not_counted_as_update(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        counts = bar_service.sync_bars(self.db, [_element()])
        self.assertEqual(counts["unchanged"], 1)
        self.assertEqual(counts["updated"], 0)

    def test_closes_bar_missing_from_osm(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        counts = bar_service.sync_bars(self.db, [])
        self.assertEqual(counts["closed"], 1)
        self.assertTrue(self._get_bar().is_closed)

    def test_already_closed_bar_stays_closed_and_unchanged(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        bar_service.sync_bars(self.db, [])
        counts = bar_service.sync_bars(self.db, [])
        self.assertEqual(counts["closed"], 0)
        self.assertEqual(counts["unchanged"], 1)

    def test_reopens_bar_returning_to_osm(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        bar_service.sync_bars(self.db, [])
        counts = bar_service.sync_bars(self.db, [_element()])
        self.assertEqual(counts["reopened"], 1)
        self.assertFalse(self._get_bar().is_closed)

    def test_same_osm_id_different_type_are_distinct(self) -> None:
        counts = bar_service.sync_bars(self.db, [_element(1), _element(1, osm_type="way", name="Le Relais")])
        self.assertEqual(counts["inserted"], 2)

    def test_dry_run_writes_nothing(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        counts = bar_service.sync_bars(self.db, [_element(name="Renamed"), _element(2, name="Le Relais")], dry_run=True)
        self.assertEqual(counts["inserted"], 1)
        self.assertEqual(counts["updated"], 1)
        self.assertEqual(self.db.query(Bar).count(), 1)
        self.assertEqual(self._get_bar().name, "Le Comptoir")

    def test_other_city_is_left_alone(self) -> None:
        bar_service.sync_bars(self.db, [_element(99, city="Lyon")], city="Lyon")
        counts = bar_service.sync_bars(self.db, [_element()], city="Paris")
        self.assertEqual(counts["inserted"], 1)
        self.assertEqual(counts["closed"], 0)
        lyon_bar = self.db.query(Bar).filter(Bar.city == "Lyon").one()
        self.assertFalse(lyon_bar.is_closed)


class TestSearchBars(BaseTestDatabase):
    def test_matches_case_insensitive_substring(self) -> None:
        bar_service.sync_bars(self.db, [_element(1), _element(2, name="Brasserie Lipp")])
        results = bar_service.search_bars(self.db, q="comptoir")
        self.assertEqual([b.name for b in results], ["Le Comptoir"])

    def test_excludes_closed_bars(self) -> None:
        bar_service.sync_bars(self.db, [_element()])
        bar_service.sync_bars(self.db, [])
        self.assertEqual(bar_service.search_bars(self.db, q="comptoir"), ())
