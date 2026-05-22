from __future__ import annotations

from app.core.security import verify_password
from app.schemas.user import UserCreate
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


class TestCreateUser(BaseTestDatabase):
    def test_returns_user_with_id(self) -> None:
        user = user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        self.assertIsNotNone(user.id)

    def test_stores_hashed_password(self) -> None:
        user = user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        self.assertNotEqual(user.hashed_password, "secret")
        self.assertTrue(verify_password("secret", user.hashed_password))

    def test_persists_username(self) -> None:
        user = user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        self.assertEqual(user.username, "alice")


class TestGetByUsername(BaseTestDatabase):
    def test_returns_existing_user(self) -> None:
        user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        found = user_service.get_by_username(self.db, "alice")
        self.assertIsNotNone(found)
        self.assertEqual(found.username, "alice")

    def test_returns_none_for_unknown_username(self) -> None:
        result = user_service.get_by_username(self.db, "nobody")
        self.assertIsNone(result)


class TestDuplicateUsername(BaseTestDatabase):
    def test_raises_on_duplicate_username(self) -> None:
        user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        with self.assertRaises(Exception):
            user_service.create_user(self.db, UserCreate(username="alice", password="other"))


class TestVerifyPassword(BaseTestDatabase):
    def test_correct_password_returns_true(self) -> None:
        user = user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        self.assertTrue(verify_password("secret", user.hashed_password))

    def test_wrong_password_returns_false(self) -> None:
        user = user_service.create_user(self.db, UserCreate(username="alice", password="secret"))
        self.assertFalse(verify_password("wrong", user.hashed_password))
