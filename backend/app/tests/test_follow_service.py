from __future__ import annotations

from app.schemas.user import UserCreate
from app.services import follow as follow_service
from app.services import user as user_service
from app.tests.base import BaseTestDatabase


class TestFollowUser(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.alice = user_service.create_user(self.db, UserCreate(username="alice", password="pass"))
        self.bob = user_service.create_user(self.db, UserCreate(username="bob", password="pass"))

    def test_follow_creates_relationship(self) -> None:
        result = follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        self.assertIsNotNone(result)
        self.assertTrue(follow_service.is_following(self.db, self.alice.id, self.bob.id))

    def test_follow_already_following_returns_none(self) -> None:
        follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        result = follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        self.assertIsNone(result)

    def test_follow_is_not_symmetric(self) -> None:
        follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        self.assertFalse(follow_service.is_following(self.db, self.bob.id, self.alice.id))


class TestUnfollowUser(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.alice = user_service.create_user(self.db, UserCreate(username="alice", password="pass"))
        self.bob = user_service.create_user(self.db, UserCreate(username="bob", password="pass"))

    def test_unfollow_removes_relationship(self) -> None:
        follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        result = follow_service.unfollow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        self.assertTrue(result)
        self.assertFalse(follow_service.is_following(self.db, self.alice.id, self.bob.id))

    def test_unfollow_not_following_returns_false(self) -> None:
        result = follow_service.unfollow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        self.assertFalse(result)


class TestListFollowing(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.alice = user_service.create_user(self.db, UserCreate(username="alice", password="pass"))
        self.bob = user_service.create_user(self.db, UserCreate(username="bob", password="pass"))
        self.carol = user_service.create_user(self.db, UserCreate(username="carol", password="pass"))

    def test_empty_when_not_following_anyone(self) -> None:
        self.assertEqual(follow_service.list_following(self.db, self.alice.id), [])

    def test_returns_followed_users(self) -> None:
        follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.carol.id)
        following = follow_service.list_following(self.db, self.alice.id)
        usernames = {u.username for u in following}
        self.assertEqual(usernames, {"bob", "carol"})

    def test_only_returns_users_i_follow(self) -> None:
        follow_service.follow_user(self.db, follower_id=self.bob.id, followed_id=self.alice.id)
        self.assertEqual(follow_service.list_following(self.db, self.alice.id), [])


class TestSearchUsers(BaseTestDatabase):
    def setUp(self) -> None:
        super().setUp()
        self.alice = user_service.create_user(self.db, UserCreate(username="alice", password="pass"))
        self.bob = user_service.create_user(self.db, UserCreate(username="bob", password="pass"))
        self.bobby = user_service.create_user(self.db, UserCreate(username="bobby", password="pass"))

    def test_returns_matching_users(self) -> None:
        results = follow_service.search_users(self.db, query="bob", current_user_id=self.alice.id)
        usernames = {r.username for r in results}
        self.assertIn("bob", usernames)
        self.assertIn("bobby", usernames)

    def test_excludes_current_user(self) -> None:
        results = follow_service.search_users(self.db, query="alice", current_user_id=self.alice.id)
        self.assertEqual(len(results), 0)

    def test_is_following_flag_correct(self) -> None:
        follow_service.follow_user(self.db, follower_id=self.alice.id, followed_id=self.bob.id)
        results = follow_service.search_users(self.db, query="bob", current_user_id=self.alice.id)
        bob_result = next(r for r in results if r.username == "bob")
        bobby_result = next(r for r in results if r.username == "bobby")
        self.assertTrue(bob_result.is_following)
        self.assertFalse(bobby_result.is_following)

    def test_case_insensitive_search(self) -> None:
        results = follow_service.search_users(self.db, query="BOB", current_user_id=self.alice.id)
        usernames = {r.username for r in results}
        self.assertIn("bob", usernames)
