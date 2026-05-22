from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_follow import UserFollow
from app.schemas.user import UserSearchResult


def is_following(db: Session, follower_id: int, followed_id: int) -> bool:
    return (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == follower_id, UserFollow.followed_id == followed_id)
        .first()
        is not None
    )


def follow_user(db: Session, follower_id: int, followed_id: int) -> UserFollow | None:
    if is_following(db, follower_id, followed_id):
        return None
    follow = UserFollow(follower_id=follower_id, followed_id=followed_id)
    db.add(follow)
    db.commit()
    return follow


def unfollow_user(db: Session, follower_id: int, followed_id: int) -> bool:
    follow = (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == follower_id, UserFollow.followed_id == followed_id)
        .first()
    )
    if follow is None:
        return False
    db.delete(follow)
    db.commit()
    return True


def list_following(db: Session, user_id: int) -> list[User]:
    return (
        db.query(User)
        .join(UserFollow, UserFollow.followed_id == User.id)
        .filter(UserFollow.follower_id == user_id)
        .order_by(User.username)
        .all()
    )


def search_users(db: Session, query: str, current_user_id: int) -> tuple[UserSearchResult, ...]:
    users = (
        db.query(User)
        .filter(User.username.ilike(f"%{query}%"), User.id != current_user_id)
        .order_by(User.username)
        .limit(5)
        .all()
    )
    return tuple(
        UserSearchResult(id=u.id, username=u.username, is_following=is_following(db, current_user_id, u.id))
        for u in users
    )
