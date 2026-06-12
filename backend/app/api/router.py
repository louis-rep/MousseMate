from fastapi import APIRouter

from app.api import auth, bar, entry, follow, geo

router = APIRouter()

router.include_router(auth.router)
router.include_router(entry.router, tags=["entries"])
router.include_router(follow.router, tags=["mates"])
router.include_router(bar.router, tags=["bars"])
router.include_router(geo.router, tags=["map"])
