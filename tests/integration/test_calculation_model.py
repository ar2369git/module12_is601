import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db import Base, get_db
from main import app
from app.models.calculation import Calculation

TEST_DB = "postgresql://postgres:postgres@localhost:5432/test_db"
engine = create_engine(TEST_DB)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_calculation_insert(db_session):
    # Compute on demand: use factory
    from app.factory.calculation_factory import compute
    calc = Calculation(a=4, b=5, type="Add", result=compute("Add", 4, 5))
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)

    assert calc.result == 9
    assert calc.a == 4

def test_invalid_type(db_session):
    with pytest.raises(ValueError):
        from app.factory.calculation_factory import compute
        compute("Foo", 1, 1)
