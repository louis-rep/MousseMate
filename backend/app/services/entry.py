from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.models.entry import Entry
from app.models.user import User
from app.schemas.entry import EntryCreate, EntryRead, EntryUpdate, VenueRead
from app.services import follow as follow_service
from app.services import like as like_service


def get_entry(db: Session, entry_id: int, user_id: int) -> Entry | None:
    return db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).first()


def list_entries(db: Session, current_user_id: int, user_id: int | None = None) -> tuple[VenueRead, ...]:
    if user_id is None:
        mates = follow_service.list_following(db, current_user_id)
        user_ids = [current_user_id, *(m.id for m in mates)]
    else:
        user_ids = [user_id]

    entries = db.query(Entry).filter(Entry.user_id.in_(user_ids)).all()
    if not entries:
        return ()

    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u.username for u in users}

    bar_ids = {e.bar_id for e in entries}
    bar_names = dict(db.query(Bar.id, Bar.name).filter(Bar.id.in_(bar_ids)).all())

    entry_ids = [e.id for e in entries]
    like_counts = like_service.get_like_counts(db, entry_ids)
    liked_ids = like_service.get_liked_entry_ids(db, current_user_id, entry_ids)

    raw = [{"user_id": e.user_id, **EntryRead.model_validate(e).model_dump()} for e in entries]
    entries_df = pd.DataFrame(raw)
    entries_df["username"] = entries_df.user_id.map(user_map)
    entries_df["bar"] = entries_df.bar_id.map(bar_names)
    entries_df["like_count"] = entries_df.id.map(like_counts).fillna(0).astype(int)
    entries_df["liked_by_me"] = entries_df.id.isin(liked_ids)
    entries_df["drink_date"] = entries_df.drink_datetime.dt.date
    entries_df = entries_df.sort_values(
        ["drink_date", "bar", "drink_datetime"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    # group on bar_id (not name) so two distinct bars sharing a name stay separate venues
    entries_df["venue_id"] = (
        (entries_df.bar_id != entries_df.bar_id.shift()) | (entries_df.drink_date != entries_df.drink_date.shift())
    ).cumsum()

    venues: list[VenueRead] = []
    for _, group in entries_df.groupby("venue_id", sort=False):
        group_sorted = group.sort_values("drink_datetime")
        records = group_sorted.astype(object).where(pd.notna(group_sorted), other=None).to_dict("records")
        venue_entries = tuple(EntryRead.model_validate(r) for r in records)
        venues.append(VenueRead(date=group.drink_date.iloc[0], bar=group.bar.iloc[0], entries=venue_entries))

    return tuple(venues)


def create_entry(db: Session, data: EntryCreate, user_id: int) -> Entry:
    entry = Entry(**data.model_dump(), user_id=user_id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry_id: int, data: EntryUpdate, user_id: int) -> Entry | None:
    entry = get_entry(db, entry_id, user_id)
    if entry is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: int, user_id: int) -> bool:
    entry = get_entry(db, entry_id, user_id)
    if entry is None:
        return False
    db.delete(entry)
    db.commit()
    return True
