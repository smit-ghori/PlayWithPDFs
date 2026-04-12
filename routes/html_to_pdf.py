from io import BytesIO
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, send_file

html_to_pdf_bp = Blueprint("html_to_pdf", __name__)


def normalize_url(url):
    cleaned_url = (url or "").strip()
    if not cleaned_url:
        raise ValueError("Please enter a website URL.")

    if not cleaned_url.startswith(("http://", "https://")):
        cleaned_url = f"https://{cleaned_url}"

    parsed_url = urlparse(cleaned_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Please enter a valid website URL.")

    return cleaned_url


def generate_pdf(url):
    normalized_url = normalize_url(url)

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Add it to requirements and run "
            "'python -m playwright install --with-deps chromium'."
        ) from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )

            try:
                page = browser.new_page(viewport={"width": 1440, "height": 2000})
                page.emulate_media(media="screen")
                page.goto(normalized_url, wait_until="domcontentloaded", timeout=60000)

                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except PlaywrightError:
                    # Some sites keep background requests open, so don't block PDF creation.
                    pass

                page.wait_for_timeout(1000)

                return page.pdf(
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise RuntimeError(
            f"Failed to open the page for PDF conversion: {exc}"
        ) from exc


@html_to_pdf_bp.route("/html_to_pdf", methods=["GET", "POST"])
def html_to_pdf():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        # print("--------------------------------------------")
        # print(url)
        # print("--------------------------------------------")

        try:
            pdf_bytes = generate_pdf(url)
        except ValueError as exc:
            return render_template("html_to_pdf.html", error=str(exc), url=url), 400
        except RuntimeError as exc:
            return render_template("html_to_pdf.html", error=str(exc), url=url), 500

        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="converted.pdf",
            mimetype="application/pdf",
        )

    return render_template("html_to_pdf.html")
