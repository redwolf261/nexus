import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

POSTGRES_USER = os.getenv("POSTGRES_USER", "nexus_app")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nexus_password")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "nexus_db")

# Allow direct override via DATABASE_URL or fallback to SQLite if PostgreSQL not running
USE_SQLITE_ENV = os.getenv("USE_SQLITE", "false").lower() in ("true", "1")
if os.getenv("TESTING") or "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") or USE_SQLITE_ENV:
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus_demo.db")
else:
    SQLALCHEMY_DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# Append sslmode=require for Neon if using the default parsing and it's a neon host, or they can just put it in DATABASE_URL
if "neon.tech" in SQLALCHEMY_DATABASE_URL and "?sslmode=require" not in SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL += "?sslmode=require"

try:
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
except Exception:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./nexus_demo.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
