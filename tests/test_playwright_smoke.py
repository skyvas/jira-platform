from http.server import HTTPServer
import os
import threading
import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

import main
from main import WasmerEdgeHandler, WasmerState


@pytest.fixture(scope="function")
def live_server():
    """Start an isolated HTTP server on an ephemeral OS-assigned port, or use CLOUD_URL if specified."""
    cloud_url = os.environ.get("CLOUD_URL")
    if cloud_url:
        yield cloud_url.rstrip("/")
        return

    main.STATE = WasmerState()
    server = HTTPServer(("127.0.0.1", 0), WasmerEdgeHandler)
    host, port = server.server_address
    url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield url
    server.shutdown()
    server.server_close()


def test_login_page_is_rendered_in_browser(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server, wait_until="load", timeout=10000)

        assert page.title() == "Orbit // Enterprise Agile & Kanban OS"
        assert page.locator("#standalone-login-form").count() == 1
        assert page.locator("#standalone-username").count() == 1
        assert page.locator("#standalone-password").count() == 1

        browser.close()


def test_page_contains_login_heading(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server, wait_until="load", timeout=10000)

        heading = page.get_by_role("heading", name="Sign In")
        heading.wait_for(state="visible", timeout=10000)
        assert heading.is_visible()

        browser.close()
