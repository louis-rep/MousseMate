from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.bar import BarRead
from app.services import bar as bar_service

router = APIRouter()


@router.get("/bars", response_model=tuple[BarRead, ...])
def search_bars(
    q: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[BarRead, ...]:
    return bar_service.search_bars(db, q=q)
