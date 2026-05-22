from fastapi import APIRouter

from app.api import auth, entry

router = APIRouter()

router.include_router(auth.router)
router.include_router(entry.router, tags=["entries"])
