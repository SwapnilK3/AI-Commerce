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
from routers import auth, webhooks, dashboard, communications, simulate, merchant_config, inbox

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-35s │ %(levelname)-7s │ %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize providers and queue on startup
    logger.info("Initializing communication providers...")
    get_providers()
    
    logger.info("Initializing background task queue...")
    create_queue(settings.REDIS_URL)
    
    # Start the worker task
    app.state.worker_task = asyncio.create_task(process_queue_worker())
    # Background worker processes tasks if any are added to the queue
    
    logger.info("Creating database tables if needed...")
    create_tables()
    
    yield
    
    # Shutdown
    if hasattr(app.state, "worker_task"):
        app.state.worker_task.cancel()

app = FastAPI(
    title="AI Smart Local Commerce Platform",
    description="Backend API for managing events, omnichannel inbox, and communications.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── Routers ────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(communications.router)
app.include_router(simulate.router)
app.include_router(merchant_config.router)
app.include_router(inbox.router)


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


@app.get("/inbox")
async def serve_inbox():
    return FileResponse(str(FRONTEND_DIR / "inbox.html"))


@app.get("/simulate")
async def serve_simulate():
    return FileResponse(str(FRONTEND_DIR / "simulate.html"))


@app.get("/settings")
async def serve_settings():
    return FileResponse(str(FRONTEND_DIR / "settings.html"))


@app.get("/login.html")
async def serve_login():
    """Serve login page for merchant authentication."""
    return FileResponse(str(FRONTEND_DIR / "login.html"))


@app.get("/register.html")
async def serve_register():
    """Serve registration page for new merchants."""
    return FileResponse(str(FRONTEND_DIR / "register.html"))
