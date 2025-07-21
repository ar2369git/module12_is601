# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from app.models.user import User          # noqa: F401,E402
from app.models.calculation import Calculation  # noqa: F401,E402

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    # Ensure tables exist before every session (cheap no-op after first time)
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
