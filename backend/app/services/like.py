from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.like import UserEntryLike


def is_liked(db: Session, user_id: int, entry_id: int) -> bool:
    return (
        db.query(UserEntryLike)
        .filter(UserEntryLike.user_id == user_id, UserEntryLike.entry_id == entry_id)
        .first()
        is not None
    )


def like_entry(db: Session, user_id: int, entry_id: int) -> UserEntryLike | None:
    if is_liked(db, user_id, entry_id):
        return None
    like = UserEntryLike(user_id=user_id, entry_id=entry_id)
    db.add(like)
    db.commit()
    return like


def unlike_entry(db: Session, user_id: int, entry_id: int) -> bool:
    like = (
        db.query(UserEntryLike)
        .filter(UserEntryLike.user_id == user_id, UserEntryLike.entry_id == entry_id)
        .first()
    )
    if like is None:
        return False
    db.delete(like)
    db.commit()
    return True


def get_like_counts(db: Session, entry_ids: list[int]) -> dict[int, int]:
    if not entry_ids:
        return {}
    rows = (
        db.query(UserEntryLike.entry_id, func.count().label("cnt"))
        .filter(UserEntryLike.entry_id.in_(entry_ids))
        .group_by(UserEntryLike.entry_id)
        .all()
    )
    return {row.entry_id: row.cnt for row in rows}


def get_liked_entry_ids(db: Session, user_id: int, entry_ids: list[int]) -> set[int]:
    if not entry_ids:
        return set()
    rows = (
        db.query(UserEntryLike.entry_id)
        .filter(UserEntryLike.user_id == user_id, UserEntryLike.entry_id.in_(entry_ids))
        .all()
    )
    return {row.entry_id for row in rows}
