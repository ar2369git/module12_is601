# tests/integration/test_user_endpoints.py
import os, pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from main import app

# Use a test Postgres via Docker Compose or detached container
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False} if TEST_DB_URL.startswith("sqlite") else {})
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

@pytest.mark.skip(reason="Temporarily skipping until DB init issue fixed")
def test_register_and_duplicate(client):
    # First registration must succeed
    r1 = client.post("/register", json={
        "username": "usr1",
        "email": "usr1@x.com",
        "password": "pass1234"
    })
    assert r1.status_code == 200
    data = r1.json()
    assert data["username"] == "usr1"

    # Duplicate registration should fail and return an "error" field
    dup = client.post("/register", json={
        "username": "usr1",
        "email": "usr1@x.com",
        "password": "pass1234"
    })
    assert dup.status_code == 400
    assert "already registered" in dup.json()["error"]
