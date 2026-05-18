import json
import zipfile
from io import BytesIO

import fitz
from flask import Blueprint, render_template, request, send_file

redact_pdf_bp = Blueprint("redact_pdf", __name__)


def _safe_filename(filename):
    return filename or "document.pdf"


def _clamp_rect(page, rect):
    page_rect = page.rect
    x0 = max(page_rect.x0, min(rect.x0, page_rect.x1 - 1))
    y0 = max(page_rect.y0, min(rect.y0, page_rect.y1 - 1))
    x1 = max(x0 + 1, min(rect.x1, page_rect.x1))
    y1 = max(y0 + 1, min(rect.y1, page_rect.y1))
    return fitz.Rect(x0, y0, x1, y1)


def _rect_from_pdfjs_bbox(page, bbox):
    page_height = page.rect.height
    x = float(bbox["x"])
    y = float(bbox["y"])
    width = float(bbox["width"])
    height = float(bbox["height"])

    # PDF.js text coordinates use a bottom-left PDF origin, while PyMuPDF uses
    # a top-left page coordinate system. The frontend sends the text baseline,
    # so subtract the text height to get the top edge.
    pad_x = max(width * 0.04, 0.8)
    pad_y = max(height * 0.12, 1.0)
    top = page_height - y - height

    rect = fitz.Rect(
        x - pad_x,
        top - pad_y,
        x + width + pad_x,
        top + height + pad_y,
    )
    return _clamp_rect(page, rect)


def _redact_pdf_file(pdf_file, redactions):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")

    redactions_by_page = {}
    for item in redactions:
        try:
            page_number = int(item.get("page", 0))
        except (TypeError, ValueError):
            continue

        if page_number < 1:
            continue

        redactions_by_page.setdefault(page_number, []).extend(item.get("bboxes", []))

    for page_number, bboxes in redactions_by_page.items():
        page_index = page_number - 1

        if page_index < 0 or page_index >= len(pdf_document):
            continue

        page = pdf_document[page_index]

        for bbox in bboxes:
            try:
                rect = _rect_from_pdfjs_bbox(page, bbox)
            except (KeyError, TypeError, ValueError):
                continue

            page.add_redact_annot(rect, fill=(0, 0, 0))

        page.apply_redactions()

    output_pdf = BytesIO()
    pdf_document.save(output_pdf, garbage=4, deflate=True)
    pdf_document.close()
    output_pdf.seek(0)
    return output_pdf


@redact_pdf_bp.route("/redact_pdf", methods=["GET", "POST"])
def redact_pdf():
    if request.method == "POST":
        pdf_files = request.files.getlist("pdfs")

        if not pdf_files:
            return "No PDF uploaded", 400

        try:
            redactions = json.loads(request.form.get("redact_data", "[]"))
        except json.JSONDecodeError:
            return "Invalid redact data", 400

        if not redactions:
            return "No text selected for redaction", 400

        processed_files = []

        try:
            for pdf_file in pdf_files:
                output_pdf = _redact_pdf_file(pdf_file, redactions)
                processed_files.append(
                    (f"redacted_{_safe_filename(pdf_file.filename)}", output_pdf)
                )
        except Exception as error:
            return f"Error redacting PDF: {error}", 400

        if len(processed_files) == 1:
            filename, file_stream = processed_files[0]

            return send_file(
                file_stream,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_stream in processed_files:
                zip_file.writestr(filename, file_stream.getvalue())

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="redacted_pdfs.zip",
            mimetype="application/zip",
        )

    return render_template("redact_pdf.html")
