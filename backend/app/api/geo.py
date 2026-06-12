from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.geo import MapScope, VenueMapResponse
from app.services import geo as geo_service

router = APIRouter()


@router.get("/map/venues", response_model=VenueMapResponse)
def get_venue_map(
    scope: MapScope = "mates",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VenueMapResponse:
    return geo_service.get_venue_map(db, current_user.id, scope)
