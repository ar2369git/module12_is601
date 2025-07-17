import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from main import app

# Use a test Postgres via GitHub Actions service or local Docker
TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/test_db"
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_register_and_duplicate(client):
    # First registration
    r1 = client.post("/register", json={
        "username": "u1",
        "email": "u1@x.com",
        "password": "pass1234"
    })
    assert r1.status_code == 200
    data = r1.json()
    assert data["username"] == "u1"
    # Duplicate should fail
    r2 = client.post("/register", json={
        "username": "u1",
        "email": "u1@x.com",
        "password": "pass1234"
    })
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"]
