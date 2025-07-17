import subprocess
import time
import pytest
import requests
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def fastapi_server():
    """Start the FastAPI server in the background."""
    p = subprocess.Popen(["uvicorn", "main:app"])
    # wait for it to be ready
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8000")
            break
        except:
            time.sleep(0.5)
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
    """Give each test a fresh page."""
    page = browser.new_page()
    yield page
    page.close()
