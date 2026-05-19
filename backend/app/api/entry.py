from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entry import EntryCreate, EntryRead, EntryUpdate, StatsSummary
from app.services import analytics
from app.services import entry as entry_service

router = APIRouter()


@router.get("/entries", response_model=list[EntryRead])
def list_entries(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> list[EntryRead]:
    return entry_service.list_entries(db, skip=skip, limit=limit)


@router.post("/entry", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(data: EntryCreate, db: Session = Depends(get_db)) -> EntryRead:
    return entry_service.create_entry(db, data)


# NOTE: /entry/stats/summary MUST be registered before /entry/{entry_id}
@router.get("/entry/stats/summary", response_model=StatsSummary)
def get_stats_summary(db: Session = Depends(get_db)) -> StatsSummary:
    return analytics.get_stats_summary(db)


@router.get("/entry/{entry_id}", response_model=EntryRead)
def get_entry(entry_id: int, db: Session = Depends(get_db)) -> EntryRead:
    entry = entry_service.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found")
    return entry


@router.patch("/entry/{entry_id}", response_model=EntryRead)
def update_entry(entry_id: int, data: EntryUpdate, db: Session = Depends(get_db)) -> EntryRead:
    entry = entry_service.update_entry(db, entry_id, data)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found")
    return entry


@router.delete("/entry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)) -> None:
    if not entry_service.delete_entry(db, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found")
