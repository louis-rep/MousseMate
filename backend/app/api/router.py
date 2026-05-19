from fastapi import APIRouter

from app.api import entry

router = APIRouter()

router.include_router(entry.router, tags=["entries"])
