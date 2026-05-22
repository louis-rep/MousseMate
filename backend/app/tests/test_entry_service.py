from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.entry import EntryCreate, EntryUpdate
from app.schemas.user import UserCreate
from app.services import entry as entry_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _make_entry(**kwargs) -> EntryCreate:
    defaults = {"type": "IPA", "volume": 50.0, "drink_datetime": datetime.now(UTC).replace(tzinfo=None)}
    return EntryCreate(**{**defaults, **kwargs})


class TestCreateEntry(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_returns_entry_with_id(self) -> None:
        entry = entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        self.assertIsNotNone(entry.id)

    def test_persists_fields(self) -> None:
        entry = entry_service.create_entry(
            self.db, _make_entry(type="Stout", volume=33.0, name="Guinness"), user_id=self.user.id
        )
        self.assertEqual(entry.type, "Stout")
        self.assertEqual(entry.volume, 33.0)
        self.assertEqual(entry.name, "Guinness")

    def test_scopes_to_user(self) -> None:
        entry = entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        self.assertEqual(entry.user_id, self.user.id)


class TestGetEntry(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_returns_created_entry(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        fetched = entry_service.get_entry(self.db, created.id, user_id=self.user.id)
        self.assertEqual(fetched.id, created.id)

    def test_returns_none_for_missing_id(self) -> None:
        result = entry_service.get_entry(self.db, 99999, user_id=self.user.id)
        self.assertIsNone(result)

    def test_returns_none_for_other_users_entry(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry = entry_service.create_entry(self.db, _make_entry(), user_id=other.id)
        result = entry_service.get_entry(self.db, entry.id, user_id=self.user.id)
        self.assertIsNone(result)


class TestListEntries(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_returns_all_entries(self) -> None:
        entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        entries = entry_service.list_entries(self.db, user_id=self.user.id)
        self.assertEqual(len(entries), 2)

    def test_empty_when_none_created(self) -> None:
        entries = entry_service.list_entries(self.db, user_id=self.user.id)
        self.assertEqual(entries, [])

    def test_respects_limit(self) -> None:
        for _ in range(5):
            entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        entries = entry_service.list_entries(self.db, user_id=self.user.id, limit=2)
        self.assertEqual(len(entries), 2)

    def test_does_not_return_other_users_entries(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry_service.create_entry(self.db, _make_entry(), user_id=other.id)
        entries = entry_service.list_entries(self.db, user_id=self.user.id)
        self.assertEqual(entries, [])


class TestUpdateEntry(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_updates_fields(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(type="IPA"), user_id=self.user.id)
        updated = entry_service.update_entry(self.db, created.id, EntryUpdate(type="Lager"), user_id=self.user.id)
        self.assertEqual(updated.type, "Lager")

    def test_returns_none_for_missing_id(self) -> None:
        result = entry_service.update_entry(self.db, 99999, EntryUpdate(type="Lager"), user_id=self.user.id)
        self.assertIsNone(result)

    def test_ignores_unset_fields(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(type="IPA", volume=50.0), user_id=self.user.id)
        updated = entry_service.update_entry(self.db, created.id, EntryUpdate(volume=33.0), user_id=self.user.id)
        self.assertEqual(updated.type, "IPA")
        self.assertEqual(updated.volume, 33.0)

    def test_cannot_update_other_users_entry(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry = entry_service.create_entry(self.db, _make_entry(type="IPA"), user_id=other.id)
        result = entry_service.update_entry(self.db, entry.id, EntryUpdate(type="Lager"), user_id=self.user.id)
        self.assertIsNone(result)


class TestDeleteEntry(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))

    def test_deletes_entry(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(), user_id=self.user.id)
        result = entry_service.delete_entry(self.db, created.id, user_id=self.user.id)
        self.assertTrue(result)
        self.assertIsNone(entry_service.get_entry(self.db, created.id, user_id=self.user.id))

    def test_returns_false_for_missing_id(self) -> None:
        result = entry_service.delete_entry(self.db, 99999, user_id=self.user.id)
        self.assertFalse(result)

    def test_cannot_delete_other_users_entry(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry = entry_service.create_entry(self.db, _make_entry(), user_id=other.id)
        result = entry_service.delete_entry(self.db, entry.id, user_id=self.user.id)
        self.assertFalse(result)
