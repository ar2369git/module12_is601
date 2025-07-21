# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    # Import models so they are registered with Base before create_all
    from app.models.user import User          # noqa: F401
    from app.models.calculation import Calculation  # noqa: F401
    Base.metadata.create_all(bind=engine)

# Ensure tables exist immediately (for TestClient usage)
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
