from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.schemas.entry import EntryCreate, EntryUpdate
from app.schemas.user import UserCreate
from app.services import entry as entry_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


def _bar(db: Session, name: str = "Le Comptoir", osm_id: int = 1) -> Bar:
    bar = Bar(osm_id=osm_id, osm_type="node", name=name, amenity="bar", latitude=48.85, longitude=2.35)
    db.add(bar)
    db.commit()
    db.refresh(bar)
    return bar


def _make_entry(bar_id: int, **kwargs) -> EntryCreate:
    defaults = {"type": "IPA", "volume": 50.0, "drink_datetime": datetime.now(UTC).replace(tzinfo=None)}
    return EntryCreate(bar_id=bar_id, **{**defaults, **kwargs})


class EntryTestBase(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.user = user_service.create_user(self.db, UserCreate(username="testuser", password="pass"))
        self.bar = _bar(self.db)


class TestCreateEntry(EntryTestBase):
    def test_returns_entry_with_id(self) -> None:
        entry = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=self.user.id)
        self.assertIsNotNone(entry.id)

    def test_persists_fields(self) -> None:
        entry = entry_service.create_entry(
            self.db, _make_entry(self.bar.id, type="Stout", volume=33.0, name="Guinness"), user_id=self.user.id
        )
        self.assertEqual(entry.type, "Stout")
        self.assertEqual(entry.volume, 33.0)
        self.assertEqual(entry.name, "Guinness")
        self.assertEqual(entry.bar_id, self.bar.id)

    def test_scopes_to_user(self) -> None:
        entry = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=self.user.id)
        self.assertEqual(entry.user_id, self.user.id)

    def test_aware_drink_datetime_is_stored_as_naive_utc(self) -> None:
        cest = timezone(timedelta(hours=2))
        data = _make_entry(self.bar.id, drink_datetime=datetime(2026, 6, 11, 20, 30, tzinfo=cest))
        entry = entry_service.create_entry(self.db, data, user_id=self.user.id)
        self.assertEqual(entry.drink_datetime, datetime(2026, 6, 11, 18, 30))
        self.assertIsNone(entry.drink_datetime.tzinfo)

    def test_entry_read_json_marks_datetimes_as_utc(self) -> None:
        from app.schemas.entry import EntryRead

        data = _make_entry(self.bar.id, drink_datetime=datetime(2026, 6, 11, 18, 30))
        entry = entry_service.create_entry(self.db, data, user_id=self.user.id)
        payload = EntryRead.model_validate(entry).model_dump_json()
        self.assertIn('"drink_datetime":"2026-06-11T18:30:00Z"', payload)
        # python-mode dumps stay naive (the pandas feed pipeline relies on this)
        dumped = EntryRead.model_validate(entry).model_dump()
        self.assertIsNone(dumped["drink_datetime"].tzinfo)


class TestGetEntry(EntryTestBase):
    def test_returns_created_entry(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=self.user.id)
        fetched = entry_service.get_entry(self.db, created.id, user_id=self.user.id)
        self.assertEqual(fetched.id, created.id)

    def test_returns_none_for_missing_id(self) -> None:
        result = entry_service.get_entry(self.db, 99999, user_id=self.user.id)
        self.assertIsNone(result)

    def test_returns_none_for_other_users_entry(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=other.id)
        result = entry_service.get_entry(self.db, entry.id, user_id=self.user.id)
        self.assertIsNone(result)


class TestListEntries(EntryTestBase):
    def test_returns_all_entries(self) -> None:
        pub_a = _bar(self.db, name="Pub A", osm_id=2)
        pub_b = _bar(self.db, name="Pub B", osm_id=3)
        entry_service.create_entry(self.db, _make_entry(pub_a.id), user_id=self.user.id)
        entry_service.create_entry(self.db, _make_entry(pub_b.id), user_id=self.user.id)
        venues = entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=self.user.id)
        total = sum(len(v.entries) for v in venues)
        self.assertEqual(total, 2)

    def test_empty_when_none_created(self) -> None:
        result = entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=self.user.id)
        self.assertEqual(result, ())

    def test_does_not_return_other_users_entries(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=other.id)
        result = entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=self.user.id)
        self.assertEqual(result, ())

    def test_feed_includes_mates_entries(self) -> None:
        from app.services import follow as follow_service

        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        follow_service.follow_user(self.db, follower_id=self.user.id, followed_id=other.id)
        entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=self.user.id)
        entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=other.id)
        venues = entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=None)
        total = sum(len(v.entries) for v in venues)
        self.assertEqual(total, 2)

    def test_feed_excludes_non_mates(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=other.id)
        venues = entry_service.list_entries(self.db, current_user_id=self.user.id, user_id=None)
        self.assertEqual(venues, ())


class TestUpdateEntry(EntryTestBase):
    def test_updates_fields(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(self.bar.id, type="IPA"), user_id=self.user.id)
        updated = entry_service.update_entry(self.db, created.id, EntryUpdate(type="Lager"), user_id=self.user.id)
        self.assertEqual(updated.type, "Lager")

    def test_updates_bar_id(self) -> None:
        other_bar = _bar(self.db, name="Le Relais", osm_id=2)
        created = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=self.user.id)
        updated = entry_service.update_entry(
            self.db, created.id, EntryUpdate(bar_id=other_bar.id), user_id=self.user.id
        )
        self.assertEqual(updated.bar_id, other_bar.id)

    def test_returns_none_for_missing_id(self) -> None:
        result = entry_service.update_entry(self.db, 99999, EntryUpdate(type="Lager"), user_id=self.user.id)
        self.assertIsNone(result)

    def test_ignores_unset_fields(self) -> None:
        created = entry_service.create_entry(
            self.db, _make_entry(self.bar.id, type="IPA", volume=50.0), user_id=self.user.id
        )
        updated = entry_service.update_entry(self.db, created.id, EntryUpdate(volume=33.0), user_id=self.user.id)
        self.assertEqual(updated.type, "IPA")
        self.assertEqual(updated.volume, 33.0)
        self.assertEqual(updated.bar_id, self.bar.id)

    def test_cannot_update_other_users_entry(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry = entry_service.create_entry(self.db, _make_entry(self.bar.id, type="IPA"), user_id=other.id)
        result = entry_service.update_entry(self.db, entry.id, EntryUpdate(type="Lager"), user_id=self.user.id)
        self.assertIsNone(result)


class TestDeleteEntry(EntryTestBase):
    def test_deletes_entry(self) -> None:
        created = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=self.user.id)
        result = entry_service.delete_entry(self.db, created.id, user_id=self.user.id)
        self.assertTrue(result)
        self.assertIsNone(entry_service.get_entry(self.db, created.id, user_id=self.user.id))

    def test_returns_false_for_missing_id(self) -> None:
        result = entry_service.delete_entry(self.db, 99999, user_id=self.user.id)
        self.assertFalse(result)

    def test_cannot_delete_other_users_entry(self) -> None:
        other = user_service.create_user(self.db, UserCreate(username="other", password="pass"))
        entry = entry_service.create_entry(self.db, _make_entry(self.bar.id), user_id=other.id)
        result = entry_service.delete_entry(self.db, entry.id, user_id=self.user.id)
        self.assertFalse(result)
