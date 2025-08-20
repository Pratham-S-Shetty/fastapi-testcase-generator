from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config.settings import settings
import structlog
import os
from sqlalchemy.engine.url import make_url

logger = structlog.get_logger()

# Ensure parent directory exists for SQLite DB files when a sqlite file URL is used.
# This avoids "unable to open database file" errors on platforms where the directory
# is not created by default (for example, cloud deploys with empty working dirs).
if "sqlite" in settings.database_url:
    try:
        url = make_url(settings.database_url)
        db_path = url.database
        if db_path:
            parent = os.path.dirname(db_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
    except Exception:
        # if parsing or mkdir fails, proceed and let SQLAlchemy raise a clear error
        pass

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_database() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    try:
        from app.models.database import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise
