import asyncio
import os
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, url_for


from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

html_to_pdf_bp = Blueprint("html_to_pdf", __name__)


def chromium_executable_path() -> str | None:
    configured_path = os.environ.get("CHROMIUM_EXECUTABLE_PATH")
    candidates = [
        configured_path,
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate

    return None


def conversion_error(message: str, status_code: int = 400):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"error": message}), status_code

    flash(message, "error")
    return redirect(url_for("html_to_pdf.html_to_pdf"))


async def generate_pdf_from_url(url: str) -> bytes:
    async with async_playwright() as p:
        try:
            launch_options = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-setuid-sandbox",
                ],
            }

            executable_path = chromium_executable_path()
            if executable_path:
                launch_options["executable_path"] = executable_path

            browser = await p.chromium.launch(
                **launch_options,
            )
        except PlaywrightError as exc:
            executable_path = chromium_executable_path() or "not found"
            raise RuntimeError(
                "Chromium could not start on the server. "
                f"CHROMIUM_EXECUTABLE_PATH={executable_path}. "
                f"Playwright error: {exc}"
            ) from exc

        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 1600})
            await page.emulate_media(media="screen")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                pass

            return await page.pdf(
                format="A4",
                print_background=True,
                scale=0.9,
                margin={
                    "top": "10mm",
                    "bottom": "10mm",
                    "left": "10mm",
                    "right": "10mm",
                },
            )
        except PlaywrightTimeoutError as exc:
            raise RuntimeError("The webpage took too long to load.") from exc
        except PlaywrightError as exc:
            raise RuntimeError(f"Failed to render the webpage: {exc}") from exc
        finally:
            await browser.close()


@html_to_pdf_bp.route("/html_to_pdf", methods=["GET", "POST"])
def html_to_pdf():
    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url:
            return conversion_error("Please provide a valid URL.")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return conversion_error("Invalid URL. Please include http:// or https://.")

        try:
            pdf_bytes = asyncio.run(generate_pdf_from_url(url))
            pdf_io = BytesIO(pdf_bytes)
            pdf_io.seek(0)

            domain = parsed.netloc.replace("www.", "").replace(".", "_")
            filename = f"{domain}.pdf"

            return send_file(
                pdf_io,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
                max_age=0,
            )
        except RuntimeError as exc:
            return conversion_error(f"Error generating PDF: {exc}", 500)
        except Exception:
            return conversion_error("Error generating PDF: unexpected server error.", 500)

    return render_template("html_to_pdf.html")
