"""
Database setup — PostgreSQL primary with SQLite auto-fallback.
Auto-detects DATABASE_URL to select the right engine.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

logger = logging.getLogger(__name__)

# ── Auto-detect database ──────────────────────────────────
db_url = settings.DATABASE_URL

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    logger.info("⟳ Database: Using SQLite (local fallback)")
else:
    logger.info("✓ Database: Using PostgreSQL")

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined by models."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
