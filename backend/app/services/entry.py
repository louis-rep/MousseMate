from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.schemas.entry import EntryCreate, EntryUpdate


def get_entry(db: Session, entry_id: int, user_id: int) -> Entry | None:
    return db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).first()


def list_entries(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> list[Entry]:
    return db.query(Entry).filter(Entry.user_id == user_id).order_by(Entry.drink_datetime.desc()).offset(skip).limit(limit).all()


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
