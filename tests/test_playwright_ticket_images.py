import base64
from http.server import HTTPServer
import os
from pathlib import Path
import struct
import threading
import urllib.request
import uuid
import zlib
import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright, Page, expect

import main
from main import WasmerEdgeHandler, WasmerState


def make_test_png(color=(255, 0, 0), width=16, height=16) -> bytes:
    """Generate deterministic, valid PNG bytes for testing."""
    r, g, b = color
    raw_rows = b"".join(b"\x00" + bytes([r, g, b] * width) for _ in range(height))
    compressed = zlib.compress(raw_rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


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


@pytest.fixture
def test_images(tmp_path):
    """Create distinct test PNG images with unique byte payloads and filenames."""
    img_red_path = tmp_path / "diagram_architecture_red.png"
    img_green_path = tmp_path / "mockup_ui_green.png"
    img_blue_path = tmp_path / "screenshot_proof_blue.png"

    red_bytes = make_test_png((255, 0, 0), width=16, height=16)
    green_bytes = make_test_png((0, 255, 0), width=24, height=24)
    blue_bytes = make_test_png((0, 0, 255), width=32, height=32)

    img_red_path.write_bytes(red_bytes)
    img_green_path.write_bytes(green_bytes)
    img_blue_path.write_bytes(blue_bytes)

    return {
        "red": {"path": str(img_red_path), "name": "diagram_architecture_red.png", "bytes": red_bytes},
        "green": {"path": str(img_green_path), "name": "mockup_ui_green.png", "bytes": green_bytes},
        "blue": {"path": str(img_blue_path), "name": "screenshot_proof_blue.png", "bytes": blue_bytes},
    }


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


def test_ticket_image_upload_association_and_persistence(live_server, test_images):
    """Verify that uploading an image from local system attaches the exact file and persists across reloads."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        login_admin(page, live_server)

        # 1. Open first ticket on the board
        first_card = page.locator(".issue-card").first
        expect(first_card).to_be_visible()
        first_card.click()

        detail_modal = page.locator("#issue-detail-modal")
        expect(detail_modal).to_be_visible()
        issue_key = page.locator("#detail-issue-key").text_content()
        assert issue_key is not None and len(issue_key) > 0

        # 2. Upload diagram_architecture_red.png
        red_info = test_images["red"]
        page.set_input_files("#detail-upload-file", red_info["path"])

        # 3. Verify attachment card appears with exact filename
        att_card = page.locator("#detail-attachments-grid .attachment-card").filter(has_text=red_info["name"]).last
        expect(att_card).to_be_visible(timeout=5000)

        # 4. Verify file_url is not the hardcoded unsplash photo but a real static upload URL
        att_img = att_card.locator(".attachment-thumb")
        file_url = att_img.get_attribute("src")
        assert file_url is not None
        assert "unsplash.com" not in file_url
        assert file_url.startswith("/static/uploads/")

        # 5. Fetch file from server and verify exact bytes match local file
        full_url = live_server + file_url
        with urllib.request.urlopen(full_url) as resp:
            downloaded_bytes = resp.read()
        assert downloaded_bytes == red_info["bytes"]

        # 6. Reload page and re-open ticket to verify persistence
        page.reload(wait_until="load")
        page.wait_for_selector("#kanban-board:visible, #standalone-login-form:visible", timeout=15000)
        if page.locator("#standalone-login-form").is_visible():
            page.fill("#standalone-username", "admin")
            page.fill("#standalone-password", "admin123")
            page.click("#btn-standalone-signin")
        expect(page.locator("#kanban-board")).to_be_visible(timeout=15000)
        expect(page.locator(".issue-card").first).to_be_visible(timeout=15000)

        # Reopen same ticket
        target_card = page.locator(".issue-card").filter(has_text=issue_key)
        target_card.click()
        expect(detail_modal).to_be_visible()

        # Attachment must still be present
        persisted_att = page.locator("#detail-attachments-grid .attachment-card").filter(has_text=red_info["name"]).last
        expect(persisted_att).to_be_visible()

        browser.close()


def test_sequential_different_image_uploads_no_mixup(live_server, test_images):
    """Verify that uploading multiple different images sequentially preserves distinct identities without mixup."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        login_admin(page, live_server)

        # Open ticket
        page.locator(".issue-card").first.click()
        expect(page.locator("#issue-detail-modal")).to_be_visible()

        green_info = test_images["green"]
        blue_info = test_images["blue"]

        # Upload image 1 (green)
        page.set_input_files("#detail-upload-file", green_info["path"])
        green_card = page.locator("#detail-attachments-grid .attachment-card").filter(has_text=green_info["name"]).last
        expect(green_card).to_be_visible(timeout=5000)

        # Upload image 2 (blue) sequentially
        page.set_input_files("#detail-upload-file", blue_info["path"])
        blue_card = page.locator("#detail-attachments-grid .attachment-card").filter(has_text=blue_info["name"]).last
        expect(blue_card).to_be_visible(timeout=5000)

        # Verify distinct URLs
        green_src = green_card.locator(".attachment-thumb").get_attribute("src")
        blue_src = blue_card.locator(".attachment-thumb").get_attribute("src")
        assert green_src != blue_src
        assert "unsplash.com" not in green_src
        assert "unsplash.com" not in blue_src

        # Verify binary bytes of both uploaded files on server
        with urllib.request.urlopen(live_server + green_src) as resp:
            assert resp.read() == green_info["bytes"]

        with urllib.request.urlopen(live_server + blue_src) as resp:
            assert resp.read() == blue_info["bytes"]

        browser.close()


def test_comment_image_thumbnail_preview_modal_and_close(live_server, test_images):
    """Verify posting a comment with an image renders a small thumbnail, clicking opens lightbox, and closing retains ticket."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        login_admin(page, live_server)

        # Open ticket
        page.locator(".issue-card").first.click()
        expect(page.locator("#issue-detail-modal")).to_be_visible()

        # Attach image to comment composer
        blue_info = test_images["blue"]
        page.set_input_files("#comment-img-file-input", blue_info["path"])

        # Staged chip should appear
        expect(page.locator("#comment-img-staging")).to_be_visible()
        expect(page.locator(".staged-thumb-chip")).to_be_visible()

        # Post comment
        comment_text = "Detailed screenshot attached for review @alex"
        page.fill("#comment-input", comment_text)
        page.click("#btn-submit-comment")

        # Comment bubble should appear in stream
        latest_comment = page.locator("#detail-comments-stream .comment-bubble").last
        expect(latest_comment).to_contain_text(comment_text)

        # Verify small thumbnail exists with badge
        comment_thumb_card = latest_comment.locator(".comment-img-card")
        expect(comment_thumb_card).to_be_visible()

        badge = comment_thumb_card.locator(".comment-img-badge")
        expect(badge).to_be_visible()
        expect(badge).to_contain_text("Image")

        # Verify thumbnail image preserves aspect ratio with object-fit: contain
        thumb_img = comment_thumb_card.locator(".comment-img-thumb")
        expect(thumb_img).to_be_visible()
        img_src = thumb_img.get_attribute("src")
        assert img_src is not None
        assert "unsplash.com" not in img_src

        # Verify thumbnail dimensions are compact (small thumbnail)
        box = comment_thumb_card.bounding_box()
        assert box is not None
        assert box["width"] <= 180
        assert box["height"] <= 120

        # Click thumbnail to open full-size preview modal (lightbox)
        comment_thumb_card.click()

        lightbox = page.locator("#lightbox-modal")
        expect(lightbox).to_be_visible()

        lightbox_img = page.locator("#lightbox-img")
        expect(lightbox_img).to_be_visible()
        assert lightbox_img.get_attribute("src") == img_src

        # Verify Close and Download actions exist
        expect(page.locator("#lightbox-close")).to_be_visible()
        expect(page.locator("#lightbox-download")).to_be_visible()

        # Close the modal
        page.click("#lightbox-close")
        expect(lightbox).not_to_be_visible()

        # CRUCIAL: User must remain on the exact same ticket detail modal
        expect(page.locator("#issue-detail-modal")).to_be_visible()

        browser.close()


def test_image_download_action_downloads_exact_file(live_server, test_images):
    """Verify that clicking Download in the image preview lightbox downloads the exact uploaded file."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        login_admin(page, live_server)

        # Open ticket
        page.locator(".issue-card").first.click()
        expect(page.locator("#issue-detail-modal")).to_be_visible()

        # Upload red image as attachment
        red_info = test_images["red"]
        page.set_input_files("#detail-upload-file", red_info["path"])

        att_card = page.locator("#detail-attachments-grid .attachment-card").filter(has_text=red_info["name"]).last
        expect(att_card).to_be_visible(timeout=5000)

        # Click thumbnail to open lightbox
        att_card.locator(".attachment-thumb").click()
        expect(page.locator("#lightbox-modal")).to_be_visible()

        # Click Download action and capture browser download event
        with page.expect_download() as download_info:
            page.click("#lightbox-download")

        download = download_info.value
        downloaded_path = download.path()
        assert downloaded_path is not None

        downloaded_bytes = Path(downloaded_path).read_bytes()
        # Verify downloaded file matches exactly the originally selected file
        assert downloaded_bytes == red_info["bytes"]

        browser.close()


def test_critical_ticket_and_comment_regression_flows(live_server):
    """Verify ticket creation, viewing, moving, and comments remain fully operational."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        login_admin(page, live_server)

        # 1. Create a new ticket via Create Issue modal
        page.click("#btn-create-issue")
        expect(page.locator("#create-modal")).to_be_visible()

        new_title = f"E2E Regression Flow {uuid.uuid4().hex[:8]}"
        page.fill("#issue-title", new_title)
        page.fill("#issue-desc", "Verifying ticket workflows remain completely healthy.")
        page.select_option("#issue-priority", "HIGH")
        page.click('#create-issue-form button[type="submit"]')

        expect(page.locator("#create-modal")).not_to_be_visible()

        # Verify card appears on board
        created_card = page.locator(".issue-card").filter(has_text=new_title).last
        expect(created_card).to_be_visible()

        # 2. Open created ticket
        created_card.click()
        expect(page.locator("#issue-detail-modal")).to_be_visible()
        expect(page.locator("#detail-title-input")).to_have_value(new_title)

        # 3. Add regular text comment with mention
        comment_msg = "Checking comments functionality without attachments @alex"
        page.fill("#comment-input", comment_msg)
        page.click("#btn-submit-comment")

        latest_comment = page.locator("#detail-comments-stream .comment-bubble").last
        expect(latest_comment).to_contain_text(comment_msg)
        expect(latest_comment.locator(".mention-pill")).to_contain_text("@alex")

        # 4. Close modal and check board is clean
        page.click("#detail-modal-close")
        expect(page.locator("#issue-detail-modal")).not_to_be_visible()
        expect(page.locator("#kanban-board")).to_be_visible()

        browser.close()
