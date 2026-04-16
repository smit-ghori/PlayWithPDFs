import asyncio
import os
from io import BytesIO
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

html_to_pdf_bp = Blueprint("html_to_pdf", __name__)


async def generate_pdf_from_url(url: str) -> bytes:
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-setuid-sandbox",
                ],
            )
        except PlaywrightError as exc:
            raise RuntimeError(
                "Chromium could not start on the server. "
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
            flash("Please provide a valid URL.", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            flash("Invalid URL. Please include http:// or https://.", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))

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
            flash(f"Error generating PDF: {exc}", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))
        except Exception:
            flash("Error generating PDF: unexpected server error.", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))

    return render_template("html_to_pdf.html")
