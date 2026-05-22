from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.schemas.entry import EntryCreate, EntryRead, EntryUpdate, VenueRead


def get_entry(db: Session, entry_id: int, user_id: int) -> Entry | None:
    return db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).first()


def list_entries(db: Session, user_id: int) -> tuple[VenueRead, ...]:
    entries = db.query(Entry).filter(Entry.user_id == user_id).all()
    if not entries:
        return ()

    entries_df = pd.DataFrame([EntryRead.model_validate(e).model_dump() for e in entries])
    entries_df["drink_date"] = entries_df.drink_datetime.dt.date
    entries_df = entries_df.sort_values(
        ["drink_date", "bar", "drink_datetime"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)

    entries_df["venue_id"] = (
        (entries_df.bar != entries_df.bar.shift()) | (entries_df.drink_date != entries_df.drink_date.shift())
    ).cumsum()

    venues: list[VenueRead] = []
    for _, group in entries_df.groupby("venue_id", sort=False):
        group_sorted = group.sort_values("drink_datetime")
        records = group_sorted.astype(object).where(pd.notna(group_sorted), other=None).to_dict("records")
        venue_entries = tuple(EntryRead.model_validate(r) for r in records)
        bar = group.bar.iloc[0]
        venues.append(
            VenueRead(date=group.drink_date.iloc[0], bar=bar if pd.notna(bar) else None, entries=venue_entries)
        )

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
