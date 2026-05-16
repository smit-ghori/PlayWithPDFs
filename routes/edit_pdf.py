import base64
import io
import json

import fitz
from flask import Blueprint, render_template, request, send_file

edit_pdf_bp = Blueprint("edit_pdf", __name__)


def decode_data_url(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("Invalid overlay image payload.")

    _, encoded = data_url.split(",", 1)
    return base64.b64decode(encoded)


def build_overlay_map(annotations_payload: dict, current_page: int, total_pages: int, edit_mode: str) -> dict[int, dict]:
    pages = annotations_payload.get("pages", {})
    overlay_map: dict[int, dict] = {}

    for page_number_str, page_data in pages.items():
        if not isinstance(page_data, dict):
            continue

        image_data = page_data.get("image")
        width = page_data.get("width")
        height = page_data.get("height")

        if not image_data or not width or not height:
            continue

        try:
            page_number = int(page_number_str)
        except (TypeError, ValueError):
            continue

        overlay_map[page_number] = {
            "image": image_data,
            "width": float(width),
            "height": float(height),
        }

    if edit_mode == "all" and current_page in overlay_map:
        current_overlay = overlay_map[current_page]
        for page_number in range(1, total_pages + 1):
            overlay_map.setdefault(page_number, current_overlay)

    return overlay_map


@edit_pdf_bp.route("/edit_pdf", methods=["GET", "POST"])
def edit_pdf():
    if request.method == "POST":
        pdf_file = request.files.get("pdfs")
        annotations_data = request.form.get("annotations_data", "")
        edit_mode = request.form.get("edit_mode", "current")
        current_page = int(request.form.get("current_page", "1"))

        if not pdf_file:
            return "No PDF uploaded.", 400

        pdf_bytes = pdf_file.read()
        if not pdf_bytes:
            return "Uploaded PDF is empty.", 400

        try:
            annotations_payload = json.loads(annotations_data) if annotations_data else {}
        except json.JSONDecodeError:
            return "Invalid editor data.", 400

        document = fitz.open(stream=pdf_bytes, filetype="pdf")

        try:
            overlay_map = build_overlay_map(
                annotations_payload,
                current_page=current_page,
                total_pages=document.page_count,
                edit_mode=edit_mode,
            )

            for page_number, overlay in overlay_map.items():
                if page_number < 1 or page_number > document.page_count:
                    continue

                page = document[page_number - 1]
                overlay_bytes = decode_data_url(overlay["image"])
                page.insert_image(
                    page.rect,
                    stream=overlay_bytes,
                    overlay=True,
                    keep_proportion=False,
                )

            output = io.BytesIO()
            document.save(output, garbage=4, deflate=True)
            output.seek(0)
        finally:
            document.close()

        filename = pdf_file.filename or "edited.pdf"
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"

        return send_file(
            output,
            as_attachment=True,
            download_name=f"edited_{filename}",
            mimetype="application/pdf",
        )

    return render_template("edit_pdf.html")
