import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MousseMate API",
    description="Strava for beer — log check-ins, track habits, discover trends.",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    logger.info("MousseMate API started")
