from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.schemas.entry import EntryCreate, EntryUpdate


def get_entry(db: Session, entry_id: int) -> Entry | None:
    return db.query(Entry).filter(Entry.id == entry_id).first()


def list_entries(db: Session, skip: int = 0, limit: int = 20) -> list[Entry]:
    return db.query(Entry).order_by(Entry.drink_datetime.desc()).offset(skip).limit(limit).all()


def create_entry(db: Session, data: EntryCreate) -> Entry:
    entry = Entry(**data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry_id: int, data: EntryUpdate) -> Entry | None:
    entry = get_entry(db, entry_id)
    if entry is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: int) -> bool:
    entry = get_entry(db, entry_id)
    if entry is None:
        return False
    db.delete(entry)
    db.commit()
    return True
