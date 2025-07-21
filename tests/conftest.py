# tests/conftest.py
import os
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
    p = subprocess.Popen(["uvicorn", "main:app"])
    for _ in range(40):
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser, fastapi_server):
    pg = browser.new_page()
    yield pg
    pg.close()


@pytest.fixture
def client():
    # Ensure a fresh DB file for each test that uses TestClient
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()

    with TestClient(app) as c:
        yield c
