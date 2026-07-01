from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added to existing tables after their first creation. Base.metadata
# .create_all only creates missing tables, not missing columns, so we patch
# these in for the SQLite dev DB to avoid dropping data.
_COLUMN_MIGRATIONS: dict[str, dict[str, str]] = {
    "scan_results": {
        "is_candidate": "BOOLEAN DEFAULT 0",
        "rvol": "FLOAT",
        "rsi_14": "FLOAT",
        "atr_14": "FLOAT",
        "atr_pct": "FLOAT",
    },
    "tickers": {
        "is_active": "BOOLEAN DEFAULT 1",
    },
}


def ensure_schema():
    """Idempotent lightweight migration for the SQLite dev DB."""
    if "sqlite" not in settings.DATABASE_URL:
        return

    insp = inspect(engine)
    table_names = set(insp.get_table_names())

    for table, columns in _COLUMN_MIGRATIONS.items():
        if table not in table_names:
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        for col, ddl in columns.items():
            if col not in existing:
                logger.info(f"Migrating {table}: adding {col} column")
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
