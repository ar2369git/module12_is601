# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent  # app/

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Import all model modules so that they register with SQLAlchemy's Base
    *before* calling create_all. This guarantees the tables exist.
    """
    # Import models here (local import to avoid circulars)
    from app.models import user, calculation  # noqa: F401

    Base.metadata.create_all(bind=engine)
