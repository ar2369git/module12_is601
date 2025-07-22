# tests/conftest.py

import subprocess
import time
import pytest
import requests
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient

from main import app
from app.db import DB_PATH, init_db


@pytest.fixture(scope="session")
def fastapi_server():
    """Background uvicorn server for e2e tests."""
    # Launch uvicorn in a subprocess
    p = subprocess.Popen(["uvicorn", "main:app"])
    # Wait until the server is responding
    for _ in range(40):
        try:
            requests.get("http://127.0.0.1:8000")
            break
        except Exception:
            time.sleep(0.25)
    yield
    # Teardown
    p.terminate()
    p.wait()


@pytest.fixture(scope="session")
def browser():
    """Launch a headless Playwright browser for e2e."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser, fastapi_server):
    """Provide a fresh page for each e2e test."""
    pg = browser.new_page()
    yield pg
    pg.close()


@pytest.fixture
def client():
    """
    Provide a TestClient with a brand-new SQLite database file.
    We delete any existing file, run init_db(), then yield the client.
    """
    # Remove old test.db if it exists
    if DB_PATH.exists():
        DB_PATH.unlink()
    # Re-create all tables
    init_db()

    with TestClient(app) as c:
        yield c
