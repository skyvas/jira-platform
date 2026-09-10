import os
import pytest
pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright


def test_login_page_is_rendered_in_browser():
    base_url = os.environ.get("CLOUD_URL", "http://127.0.0.1:8000/")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(base_url, wait_until="load", timeout=10000)

        assert page.title() == "Orbit // Enterprise Agile & Kanban OS"
        assert page.locator("#standalone-login-form").count() == 1
        assert page.locator("#standalone-username").count() == 1
        assert page.locator("#standalone-password").count() == 1

        browser.close()


def test_page_contains_login_heading():
    base_url = os.environ.get("CLOUD_URL", "http://127.0.0.1:8000/")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(base_url, wait_until="load", timeout=10000)

        heading = page.get_by_role("heading", name="Sign In")
        heading.wait_for(state="visible", timeout=10000)
        assert heading.is_visible()

        browser.close()
