"""
AI Smart Local Commerce Communication Platform — FastAPI Entry Point
Initializes providers, queue, database, and serves frontend.
"""
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import create_tables
from config import settings
from providers.factory import init_providers, get_providers
from queue_manager import create_queue, get_queue, set_worker_callback, process_queue_worker
from routers import webhooks, dashboard, communications, simulate

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-35s │ %(levelname)-7s │ %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("  AI Smart Commerce Communication Platform")
    logger.info("=" * 60)

    # 1. Create database tables
    logger.info("Creating database tables...")
    create_tables()

    # 2. Initialize providers (auto-detection)
    providers = init_providers()

    # 3. Initialize queue
    queue = create_queue(settings.REDIS_URL)

    # 4. Start background queue worker
    worker_task = asyncio.create_task(process_queue_worker())

    logger.info("=" * 60)
    logger.info("  Platform is running!")
    logger.info("  Dashboard: http://localhost:8000")
    logger.info("  API docs:  http://localhost:8000/docs")
    logger.info("")
    logger.info("  Active Providers:")
    for k, v in providers.summary().items():
        logger.info("    %-12s → %s", k, v)
    logger.info("  Queue: %s", queue.get_name())
    logger.info("=" * 60)

    yield

    # Shutdown
    worker_task.cancel()
    logger.info("Platform shutdown complete")


# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="AI Smart Commerce Communication",
    description="AI-powered communication layer for local commerce platforms",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(communications.router)
app.include_router(simulate.router)


# ── Provider info endpoint ─────────────────────────────────
@app.get("/api/providers")
async def get_active_providers():
    """Return currently active providers and their types."""
    providers = get_providers()
    queue = get_queue()
    return {
        "providers": providers.summary(),
        "queue": queue.get_name(),
        "database": "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite",
    }


# ── Static files (frontend) ───────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


# ── Serve frontend pages ──────────────────────────────────
@app.get("/")
async def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/orders")
async def serve_orders():
    return FileResponse(str(FRONTEND_DIR / "orders.html"))


@app.get("/events")
async def serve_events():
    return FileResponse(str(FRONTEND_DIR / "events.html"))


@app.get("/communications")
async def serve_communications():
    return FileResponse(str(FRONTEND_DIR / "communications.html"))


@app.get("/simulate")
async def serve_simulate():
    return FileResponse(str(FRONTEND_DIR / "simulate.html"))


@app.get("/settings")
async def serve_settings():
    return FileResponse(str(FRONTEND_DIR / "settings.html"))
