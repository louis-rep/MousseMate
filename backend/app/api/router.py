from fastapi import APIRouter

from app.api import entries

router = APIRouter()

router.include_router(entries.router, prefix="/entries", tags=["entries"])
