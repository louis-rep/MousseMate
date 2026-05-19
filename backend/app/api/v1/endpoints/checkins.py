from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.checkin import CheckInCreate, CheckInRead, CheckInUpdate, StatsSummary
from app.services import checkin as checkin_service

router = APIRouter()


@router.post("/", response_model=CheckInRead, status_code=status.HTTP_201_CREATED)
def create_checkin(data: CheckInCreate, db: Session = Depends(get_db)) -> CheckInRead:
    """Log a new beer check-in."""
    return checkin_service.create_checkin(db, data)


@router.get("/", response_model=list[CheckInRead])
def list_checkins(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[CheckInRead]:
    """Return a paginated list of check-ins."""
    return checkin_service.list_checkins(db, skip=skip, limit=limit)


# NOTE: /stats/summary MUST be registered before /{checkin_id} to avoid
# FastAPI routing the literal string "stats" as an integer path parameter.
@router.get("/stats/summary", response_model=StatsSummary)
def get_stats_summary(db: Session = Depends(get_db)) -> StatsSummary:
    """Return aggregated statistics for all check-ins."""
    return checkin_service.get_stats_summary(db)


@router.get("/{checkin_id}", response_model=CheckInRead)
def get_checkin(checkin_id: int, db: Session = Depends(get_db)) -> CheckInRead:
    """Return a single check-in by ID."""
    checkin = checkin_service.get_checkin(db, checkin_id)
    if checkin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CheckIn {checkin_id} not found",
        )
    return checkin


@router.patch("/{checkin_id}", response_model=CheckInRead)
def update_checkin(
    checkin_id: int,
    data: CheckInUpdate,
    db: Session = Depends(get_db),
) -> CheckInRead:
    """Partially update a check-in."""
    checkin = checkin_service.update_checkin(db, checkin_id, data)
    if checkin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CheckIn {checkin_id} not found",
        )
    return checkin


@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checkin(checkin_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a check-in. Returns 204 No Content on success."""
    deleted = checkin_service.delete_checkin(db, checkin_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CheckIn {checkin_id} not found",
        )
