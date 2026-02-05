"""Database connection and session management."""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from app.config import get_settings

settings = get_settings()


def clean_database_url(url: str) -> str:
    """Remove pgbouncer and other unsupported parameters from database URL."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    # Remove pgbouncer parameter - psycopg2 doesn't support it
    query_params.pop("pgbouncer", None)
    query_params.pop("pgbouncer=true", None)
    # Rebuild URL without unsupported parameters
    clean_query = urlencode(query_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        clean_query,
        parsed.fragment
    ))
    return clean_url


# Clean database URL before creating engine
database_url = clean_database_url(settings.database_url)

# Create engine with connection pooling
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
