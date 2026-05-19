from fastapi import APIRouter

from app.api.v1.endpoints import checkins

router = APIRouter()

router.include_router(checkins.router, prefix="/checkins", tags=["checkins"])
