"""Business Radar AI FastAPI app.

Responsibilities of the lifespan:
  1) Validate runtime config (JWT secret, CORS, DB URL).
  2) Wait for the database to be reachable (with retries).
  3) Run Alembic migrations (upgrade head) — no more SQLAlchemy create_all.
  4) Seed (idempotent; QA users only in non-prod).
  5) Start scheduler (daily report + dynamic discovery schedules).
  6) Start enrichment worker (background AI pipeline).
"""
import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from config import validate_config, InsecureConfigError
import models  # ensure models are imported
from routers import (
    auth_router, users_router, businesses_router, discovery_router,
    reports_router, admin_router, preferences_router, dashboard_router,
)
from scheduler import start_scheduler, stop_scheduler
import enrichment_worker
import seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("business_radar")


async def _wait_for_db(max_wait_seconds: int = 30) -> None:
    """Don't crash on a slow Postgres start — retry quickly."""
    from database import engine
    deadline = time.time() + max_wait_seconds
    last_err = None
    while time.time() < deadline:
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            return
        except Exception as e:
            last_err = e
            await asyncio.sleep(1.5)
    raise RuntimeError(f"Database not reachable after {max_wait_seconds}s: {last_err}")


def _run_alembic_upgrade() -> None:
    """Apply Alembic migrations programmatically (upgrade head).

    Works against the sync DATABASE_URL_SYNC; falls back to converting the async URL.
    """
    from alembic.config import Config
    from alembic import command
    cfg = Config(str(ROOT_DIR / "alembic.ini"))
    sync_url = os.environ.get("DATABASE_URL_SYNC")
    if not sync_url:
        async_url = os.environ.get("DATABASE_URL", "")
        sync_url = async_url.replace("+asyncpg", "")
    cfg.set_main_option("sqlalchemy.url", sync_url)
    cfg.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    command.upgrade(cfg, "head")
    log.info("Alembic: upgrade head completed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Validate configuration
    try:
        validate_config()
    except InsecureConfigError as e:
        log.error("REFUSING TO START in production with insecure config:\n%s", e)
        raise

    # 2. Wait for DB + run migrations
    try:
        await _wait_for_db()
    except Exception as e:
        log.error("DB not reachable: %s", e)
        raise
    try:
        _run_alembic_upgrade()
    except Exception as e:
        log.error("Alembic upgrade failed: %s", e)
        raise

    # 3. Seed (idempotent)
    try:
        await seed.run_seed()
    except Exception as e:
        log.warning("Seed failed (non-fatal): %s", e)

    # 4. Scheduler + worker
    try:
        await start_scheduler()
    except Exception as e:
        log.warning("Scheduler start failed: %s", e)
    try:
        await enrichment_worker.start_worker()
    except Exception as e:
        log.warning("Worker start failed: %s", e)

    yield

    await stop_scheduler()
    await enrichment_worker.stop_worker()


app = FastAPI(title="Business Radar AI", version="1.2.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


api = APIRouter(prefix="/api")


@api.get("/")
async def root():
    return {"message": "Business Radar AI", "status": "ok"}


@api.get("/healthz")
async def healthz():
    from database import engine
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "degraded", "detail": str(e)[:160]})


api.include_router(auth_router.router)
api.include_router(users_router.router)
api.include_router(businesses_router.router)
api.include_router(discovery_router.router)
api.include_router(reports_router.router)
api.include_router(admin_router.router)
api.include_router(preferences_router.router)
api.include_router(dashboard_router.router)

app.include_router(api)

# CORS — strict allow-list, never "*" with credentials in production.
_cors = [o.strip() for o in (os.environ.get("CORS_ORIGINS") or "").split(",") if o.strip()]
if not _cors:
    _cors = ["http://localhost:3000"]
_use_credentials = (os.environ.get("APP_ENV", "development").lower() != "production") or ("*" not in _cors)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=_use_credentials,
    allow_origins=_cors,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Request-ID"],
)
