"""Business Radar AI FastAPI app."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from database import engine, Base
from routers import (
    auth_router, users_router, businesses_router, discovery_router,
    reports_router, admin_router, preferences_router, dashboard_router,
)
import models  # ensure models are registered
from scheduler import start_scheduler, stop_scheduler
import seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("business_radar")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (idempotent for MVP)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed admin + sample data
    try:
        await seed.run_seed()
    except Exception as e:
        log.warning(f"Seed failed (non-fatal): {e}")
    # Start scheduler
    try:
        await start_scheduler()
    except Exception as e:
        log.warning(f"Scheduler start failed: {e}")
    yield
    await stop_scheduler()


app = FastAPI(title="Business Radar AI", version="1.0.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


api = APIRouter(prefix="/api")


@api.get("/")
async def root():
    return {"message": "Business Radar AI", "status": "ok"}


api.include_router(auth_router.router)
api.include_router(users_router.router)
api.include_router(businesses_router.router)
api.include_router(discovery_router.router)
api.include_router(reports_router.router)
api.include_router(admin_router.router)
api.include_router(preferences_router.router)
api.include_router(dashboard_router.router)

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
