import pytest
pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright


def test_login_page_is_rendered_in_browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="load", timeout=5000)

        assert page.title() == "Orbit // Enterprise Agile & Kanban OS"
        assert page.locator("#standalone-login-form").count() == 1
        assert page.locator("#standalone-username").count() == 1
        assert page.locator("#standalone-password").count() == 1

        browser.close()


def test_page_contains_login_heading():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="load", timeout=5000)

        heading = page.get_by_role("heading", name="Sign In")
        assert heading.is_visible()

        browser.close()
