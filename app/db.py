# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Create the Base **here** so other modules can import it
Base = declarative_base()

# Pick a database URL:
db_url = (
    os.getenv("TEST_DATABASE_URL")
    or os.getenv("DATABASE_URL")
)

# Fallback to local sqlite if nothing set
if not db_url:
    db_url = "sqlite:///./test.db"

# Needed for SQLite; ignored by Postgres
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
