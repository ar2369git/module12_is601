import subprocess
import time
import pytest
import requests
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient

from main import app
from app.db import init_db  # <-- import here


@pytest.fixture(scope="session")
def fastapi_server():
    """Start the FastAPI server in the background for E2E tests."""
    p = subprocess.Popen(["uvicorn", "main:app"])
    # wait for server to be ready
    for _ in range(20):
        try:
            requests.get("http://127.0.0.1:8000")
            break
        except Exception:
            time.sleep(0.25)
    yield
    p.terminate()
    p.wait()


@pytest.fixture(scope="session")
def browser():
    """Launch a headless browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser, fastapi_server):
    """Give each E2E test a fresh page."""
    page = browser.new_page()
    yield page
    page.close()


@pytest.fixture
def client():
    """API client for integration/unit tests.

    We call init_db() explicitly to ensure tables exist before the
    TestClient handles any requests.
    """
    init_db()  # <-- ensure tables are created
    with TestClient(app) as c:
        yield c
