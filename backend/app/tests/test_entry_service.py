from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.entry import EntryCreate, EntryUpdate
from app.services import entry as entry_service
from app.tests.base import BaseTestDatabase


def _make_entry(**kwargs) -> EntryCreate:
    defaults = {"type": "IPA", "volume": 50.0, "drink_datetime": datetime.now(UTC).replace(tzinfo=None)}
    return EntryCreate(**{**defaults, **kwargs})


class TestCreateEntry(BaseTestDatabase):
    def test_returns_entry_with_id(self) -> None:
        entry = entry_service.create_entry(self.db, _make_entry())
        self.assertIsNotNone(entry.id)

    def test_persists_fields(self) -> None:
        entry = entry_service.create_entry(self.db, _make_entry(type="Stout", volume=33.0, name="Guinness"))
        self.assertEqual(entry.type, "Stout")
        self.assertEqual(entry.volume, 33.0)
        self.assertEqual(entry.name, "Guinness")


class TestGetEntry(BaseTestDatabase):
    def test_returns_created_entry(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry())
        fetched = entry_service.get_entry(self.db, created.id)
        self.assertEqual(fetched.id, created.id)

    def test_returns_none_for_missing_id(self) -> None:
        result = entry_service.get_entry(self.db, 99999)
        self.assertIsNone(result)


class TestListEntries(BaseTestDatabase):
    def test_returns_all_entries(self) -> None:
        entry_service.create_entry(self.db, _make_entry())
        entry_service.create_entry(self.db, _make_entry())
        entries = entry_service.list_entries(self.db)
        self.assertEqual(len(entries), 2)

    def test_empty_when_none_created(self) -> None:
        entries = entry_service.list_entries(self.db)
        self.assertEqual(entries, [])

    def test_respects_limit(self) -> None:
        for _ in range(5):
            entry_service.create_entry(self.db, _make_entry())
        entries = entry_service.list_entries(self.db, limit=2)
        self.assertEqual(len(entries), 2)


class TestUpdateEntry(BaseTestDatabase):
    def test_updates_fields(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(type="IPA"))
        updated = entry_service.update_entry(self.db, created.id, EntryUpdate(type="Lager"))
        self.assertEqual(updated.type, "Lager")

    def test_returns_none_for_missing_id(self) -> None:
        result = entry_service.update_entry(self.db, 99999, EntryUpdate(type="Lager"))
        self.assertIsNone(result)

    def test_ignores_unset_fields(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(type="IPA", volume=50.0))
        updated = entry_service.update_entry(self.db, created.id, EntryUpdate(volume=33.0))
        self.assertEqual(updated.type, "IPA")
        self.assertEqual(updated.volume, 33.0)


class TestDeleteEntry(BaseTestDatabase):
    def test_deletes_entry(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry())
        result = entry_service.delete_entry(self.db, created.id)
        self.assertTrue(result)
        self.assertIsNone(entry_service.get_entry(self.db, created.id))

    def test_returns_false_for_missing_id(self) -> None:
        result = entry_service.delete_entry(self.db, 99999)
        self.assertFalse(result)
