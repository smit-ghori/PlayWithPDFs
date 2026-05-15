from flask import Blueprint, render_template, request, send_file
from io import BytesIO
import zipfile
import fitz

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

add_watermark_bp = Blueprint("add_watermark", __name__)


# =========================================
# POSITION HELPER
# =========================================


def get_position(position, width, height):

    positions = {
        "top-left": (50, 60),
        "top-center": (width / 2, 60),
        "top-right": (width - 120, 60),
        "middle-left": (60, height / 2),
        "middle-center": (width / 2, height / 2),
        "middle-right": (width - 120, height / 2),
        "bottom-left": (60, height - 60),
        "bottom-center": (width / 2, height - 60),
        "bottom-right": (width - 120, height - 60),
    }

    return positions.get(position, (width / 2, height / 2))


# =========================================
# WATERMARK ROUTE
# =========================================


@add_watermark_bp.route("/add_watermark", methods=["GET", "POST"])
def add_watermark():

    if request.method == "POST":

        # =====================================
        # FILES
        # =====================================

        pdf_files = request.files.getlist("pdfs")

        if not pdf_files:
            return "No PDF Uploaded"

        # =====================================
        # FORM VALUES
        # =====================================

        watermark_text = request.form.get("watermark_text", "WATERMARK")

        bold = bool(request.form.get("bold"))

        italic = bool(request.form.get("italic"))

        underline = bool(request.form.get("underline"))

        font_family = request.form.get("font_family", "Helvetica")

        watermark_color = request.form.get("watermark_color", "#000000")

        position = request.form.get("position", "middle-center")

        transparency = request.form.get("transparency", "50")

        rotation = int(request.form.get("rotation", "45"))

        layer = request.form.get("layer", "over")

        # =====================================
        # FONT STYLE
        # =====================================

        if bold:
            font_family += "-Bold"

        # =====================================
        # OPACITY
        # =====================================

        transparency_map = {"75": 0.25, "50": 0.50, "20": 0.80, "0": 1.0}

        opacity = transparency_map.get(transparency, 0.5)

        # =====================================
        # STORE OUTPUT FILES
        # =====================================

        processed_files = []

        # =====================================
        # PROCESS ALL PDFs
        # =====================================

        for pdf_file in pdf_files:

            pdf_bytes = pdf_file.read()

            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            # =================================
            # PROCESS PAGES
            # =================================

            for page in pdf_document:

                rect = page.rect

                width = rect.width
                height = rect.height

                # =============================
                # CREATE WATERMARK
                # =============================

                watermark_stream = BytesIO()

                c = canvas.Canvas(watermark_stream, pagesize=(width, height))

                c.saveState()

                c.setFillAlpha(opacity)

                c.setFillColor(HexColor(watermark_color))

                c.setFont("Helvetica", 40)

                x, y = get_position(position, width, height)

                c.translate(x, y)

                c.rotate(rotation)

                c.drawCentredString(0, 0, watermark_text)

                # Underline
                if underline:

                    text_width = c.stringWidth(watermark_text, "Helvetica", 40)

                    c.line(-text_width / 2, -5, text_width / 2, -5)

                c.restoreState()

                c.save()

                watermark_stream.seek(0)

                # =============================
                # INSERT WATERMARK
                # =============================

                overlay = fitz.open(stream=watermark_stream.read(), filetype="pdf")

                try:

                    if layer == "below":

                        page.show_pdf_page(rect, overlay, 0, overlay=False)

                    else:

                        page.show_pdf_page(rect, overlay, 0, overlay=True)

                except:

                    # fallback for scanned PDFs

                    page.show_pdf_page(rect, overlay, 0, overlay=True)

            # =================================
            # SAVE PDF TO MEMORY
            # =================================

            output_pdf = BytesIO()

            pdf_document.save(output_pdf)

            output_pdf.seek(0)

            pdf_document.close()

            # Store filename + file
            processed_files.append((f"watermarked_{pdf_file.filename}", output_pdf))

        # =====================================
        # SINGLE FILE DOWNLOAD
        # =====================================

        if len(processed_files) == 1:

            filename, file_stream = processed_files[0]

            return send_file(
                file_stream,
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )

        # =====================================
        # MULTIPLE FILES -> ZIP
        # =====================================

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

            for filename, file_stream in processed_files:

                zip_file.writestr(filename, file_stream.getvalue())

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="watermarked_pdfs.zip",
            mimetype="application/zip",
        )

    return render_template("add_watermark.html")
