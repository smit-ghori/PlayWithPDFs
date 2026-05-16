import json
import zipfile
from io import BytesIO

import fitz
from flask import Blueprint, render_template, request, send_file

crop_pdf_bp = Blueprint("crop_pdf", __name__)


def _safe_filename(filename):
    return filename or "document.pdf"


def _rect_from_ratios(page, crop):
    page_rect = page.rect
    x0 = page_rect.x0 + float(crop["x"]) * page_rect.width
    y0 = page_rect.y0 + float(crop["y"]) * page_rect.height
    x1 = x0 + float(crop["width"]) * page_rect.width
    y1 = y0 + float(crop["height"]) * page_rect.height

    x0 = max(page_rect.x0, min(x0, page_rect.x1 - 1))
    y0 = max(page_rect.y0, min(y0, page_rect.y1 - 1))
    x1 = max(x0 + 1, min(x1, page_rect.x1))
    y1 = max(y0 + 1, min(y1, page_rect.y1))

    return fitz.Rect(x0, y0, x1, y1)


def _crop_pdf_file(pdf_file, crop_data):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    mode = crop_data.get("mode", "all")

    if mode == "current":
        for page_number, page_crop in crop_data.get("page_crops", {}).items():
            try:
                page_index = int(page_number) - 1
            except (TypeError, ValueError):
                continue

            if page_crop and 0 <= page_index < len(pdf_document):
                page = pdf_document[page_index]
                page.set_cropbox(_rect_from_ratios(page, page_crop))
    else:
        common_crop = crop_data.get("all_pages_crop")

        if common_crop:
            for page in pdf_document:
                page.set_cropbox(_rect_from_ratios(page, common_crop))

    output_pdf = BytesIO()
    pdf_document.save(output_pdf)
    pdf_document.close()
    output_pdf.seek(0)
    return output_pdf


@crop_pdf_bp.route("/crop_pdf", methods=["GET", "POST"])
def crop_pdf():
    if request.method == "POST":
        pdf_files = request.files.getlist("pdfs")

        if not pdf_files:
            return "No PDF uploaded", 400

        try:
            crop_data = json.loads(request.form.get("crop_data", "{}"))
        except json.JSONDecodeError:
            return "Invalid crop data", 400

        processed_files = []

        try:
            for pdf_file in pdf_files:
                output_pdf = _crop_pdf_file(pdf_file, crop_data)
                processed_files.append(
                    (f"cropped_{_safe_filename(pdf_file.filename)}", output_pdf)
                )
        except Exception as error:
            return f"Error cropping PDF: {error}", 400

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
            download_name="cropped_pdfs.zip",
            mimetype="application/zip",
        )

    return render_template("crop_pdf.html")
