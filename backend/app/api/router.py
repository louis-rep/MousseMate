from fastapi import APIRouter

from app.api import auth, entry, follow

router = APIRouter()

router.include_router(auth.router)
router.include_router(entry.router, tags=["entries"])
router.include_router(follow.router, tags=["mates"])
