from io import BytesIO
from urllib.parse import urlparse
from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
    make_response,
)
import asyncio
from playwright.async_api import async_playwright

html_to_pdf_bp = Blueprint("html_to_pdf", __name__)


# ✅ Async function (safe + timeout handled)
async def generate_pdf_from_url(url: str) -> bytes:
    import os

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/render/project/src/.playwright"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 1600})

        await page.emulate_media(media="screen")

        try:
            # Load page safely
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Some sites never become "networkidle"
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass

        except Exception as e:
            await browser.close()
            raise Exception("Failed to load webpage")

        # Generate PDF
        pdf_bytes = await page.pdf(
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

        await browser.close()
        return pdf_bytes


# ✅ Route
@html_to_pdf_bp.route("/html_to_pdf", methods=["GET", "POST"])
def html_to_pdf():
    if request.method == "POST":
        url = request.form.get("url", "").strip()

        # ❌ Validation
        if not url:
            flash("Please provide a valid URL", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            flash("Invalid URL. Please include http:// or https://", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))

        try:
            # ✅ SAFE async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            pdf_bytes = loop.run_until_complete(generate_pdf_from_url(url))
            loop.close()

            # ✅ Prepare PDF
            pdf_io = BytesIO(pdf_bytes)
            pdf_io.seek(0)

            domain = parsed.netloc.replace("www.", "").replace(".", "_")
            filename = f"{domain}.pdf"

            # ✅ Proper response (important fix)
            response = make_response(
                send_file(
                    pdf_io,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/pdf",
                )
            )

            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            response.headers["Cache-Control"] = "no-cache"

            return response

        except Exception as e:
            flash(f"Error generating PDF: {str(e)}", "error")
            return redirect(url_for("html_to_pdf.html_to_pdf"))

    return render_template("html_to_pdf.html")
