"""
Storage layer. Uses SQLAlchemy so PostgreSQL (production, via
docker-compose) and SQLite (local dev / CI, zero setup) both work
against the same models.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import get_settings

logger = logging.getLogger("alphaflow.db")
settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnalysisRecord(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True, nullable=False)
    decision = Column(String(20), nullable=False)
    expected_return_pct = Column(Float)
    profit_probability = Column(Float)
    risk_label = Column(String(10))
    confidence_score = Column(Float)
    explanation = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """Create tables if possible. Never crash app startup because of a
    bad/unreachable DATABASE_URL — history/audit logging is a nice-to-have,
    not a hard dependency for the core analysis API to function."""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database ready: %s", _redact(settings.database_url))
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Could not connect to DATABASE_URL (%s). Falling back to local "
            "SQLite so the API can still start. Original error: %s",
            _redact(settings.database_url), exc,
        )
        fallback_url = "sqlite:///./alphaflow.db"
        engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
        SessionLocal.configure(bind=engine)
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            logger.error("SQLite fallback also failed; history endpoints will be degraded.")


def _redact(url: str) -> str:
    # Avoid printing credentials in logs.
    if "@" in url:
        scheme_and_creds, host_part = url.rsplit("@", 1)
        scheme = scheme_and_creds.split("://")[0]
        return f"{scheme}://***:***@{host_part}"
    return url


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
