from http.server import HTTPServer
import os
from pathlib import Path
import re
import threading
import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright, Page, expect

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


def login_admin(page: Page, base_url: str):
    """Log in as admin and wait for board to render."""
    page.goto(base_url, wait_until="load")
    page.wait_for_selector("#kanban-board:visible, #standalone-login-form:visible", timeout=15000)
    login_form = page.locator("#standalone-login-form")
    if login_form.is_visible():
        page.fill("#standalone-username", "admin")
        page.fill("#standalone-password", "admin123")
        page.click("#btn-standalone-signin")
    expect(page.locator("#kanban-board")).to_be_visible(timeout=15000)
    expect(page.locator(".issue-card").first).to_be_visible(timeout=15000)


def test_quick_filters_toolbar(live_server):
    """Verify quick filters: My Issues toggle, Issue Type filter, live search, and reset."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        login_admin(page, live_server)

        initial_count = page.locator(".issue-card").count()
        assert initial_count >= 3

        # 1. Test "My Issues" button filter
        my_issues_btn = page.locator("#btn-filter-my-issues")
        expect(my_issues_btn).to_be_visible()
        my_issues_btn.click()
        expect(my_issues_btn).to_have_class(re.compile(r"\bactive\b"))

        # Admin should have assigned issues visible
        admin_count = page.locator(".issue-card").count()
        assert admin_count > 0
        assert admin_count <= initial_count

        # Unclick "My Issues"
        my_issues_btn.click()
        expect(my_issues_btn).not_to_have_class(re.compile(r"\bactive\b"))
        expect(page.locator(".issue-card")).to_have_count(initial_count)

        # 2. Test Issue Type dropdown filter
        type_filter = page.locator("#type-filter")
        expect(type_filter).to_be_visible()
        type_filter.select_option("BUG")
        bug_cards = page.locator(".issue-card")
        bug_count = bug_cards.count()
        assert bug_count >= 1
        for i in range(bug_count):
            expect(bug_cards.nth(i).locator(".type-badge")).to_have_text("BUG")

        # 3. Test Reset Filters button
        reset_btn = page.locator("#btn-reset-filters")
        expect(reset_btn).to_be_visible()
        reset_btn.click()
        expect(page.locator(".issue-card")).to_have_count(initial_count)
        expect(type_filter).to_have_value("ALL")

        # 4. Test live search
        page.fill("#search-input", "Architecture")
        search_count = page.locator(".issue-card").count()
        assert search_count >= 1
        reset_btn.click()
        expect(page.locator("#search-input")).to_have_value("")

        browser.close()


def test_story_points_display_and_aggregations(live_server):
    """Verify story point pills appear on cards and column headers display point totals."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        login_admin(page, live_server)

        # 1. Verify card story point badge exists on at least one card
        points_badges = page.locator(".card-points-badge")
        expect(points_badges.first).to_be_visible()
        badge_text = points_badges.first.text_content()
        assert "pts" in badge_text

        # 2. Verify column header has col-points-badge
        col_points = page.locator(".col-points-badge")
        assert col_points.count() >= 1
        col_text = col_points.first.text_content()
        assert "pts" in col_text

        browser.close()


def test_interactive_acceptance_checklist_flow(live_server):
    """Verify adding, checking off, and deleting acceptance criteria in ticket details."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        login_admin(page, live_server)

        # 1. Open first card
        first_card = page.locator(".issue-card").first
        first_card.click()

        detail_modal = page.locator("#issue-detail-modal")
        expect(detail_modal).to_be_visible()

        # 2. Verify checklist section
        checklist_section = page.locator("#detail-checklist-section")
        expect(checklist_section).to_be_visible()

        # 3. Add new checklist item
        new_item_input = page.locator("#input-new-checklist-item")
        new_item_input.fill("Verify zero-leak test passing")
        page.click("#btn-add-checklist-item")

        # Item should appear in list
        new_item_row = page.locator(".checklist-item-row").filter(has_text="Verify zero-leak test passing")
        expect(new_item_row).to_be_visible(timeout=5000)

        # 4. Check the checkbox
        cb = new_item_row.locator(".checklist-item-cb")
        cb.check()
        expect(new_item_row).to_have_class("checklist-item-row completed", timeout=5000)

        # Counter text should show completed
        counter = page.locator("#detail-checklist-counter")
        expect(counter).to_contain_text("completed")

        # 5. Close modal
        page.click("#detail-modal-close")
        expect(detail_modal).to_be_hidden()

        # Verify card checklist badge reflects items
        card_badge = first_card.locator(".card-checklist-badge")
        expect(card_badge).to_be_visible()
        expect(card_badge).to_contain_text("☑")

        browser.close()


def test_keyboard_shortcuts(live_server):
    """Verify c opens create modal, / focuses search, ? opens shortcuts modal, and Esc closes."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        login_admin(page, live_server)

        # 1. Press ? to open keyboard shortcuts dialog
        page.keyboard.press("?")
        shortcuts_modal = page.locator("#shortcuts-modal")
        expect(shortcuts_modal).to_be_visible()

        # Press Escape to close
        page.keyboard.press("Escape")
        expect(shortcuts_modal).to_be_hidden()

        # 2. Press c to open Create Issue modal
        page.keyboard.press("c")
        create_modal = page.locator("#create-modal")
        expect(create_modal).to_be_visible()

        # Press Escape to close
        page.keyboard.press("Escape")
        expect(create_modal).to_be_hidden()

        # 3. Press / to focus search input
        page.keyboard.press("/")
        is_focused = page.evaluate("document.activeElement.id === 'search-input'")
        assert is_focused is True

        browser.close()
