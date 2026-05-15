from flask import Blueprint, render_template, request, send_file

from io import BytesIO

from PyPDF2 import PdfReader, PdfWriter

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

add_page_number_bp = Blueprint("add_page_number", __name__)


# =========================================
# CREATE PAGE NUMBER OVERLAY
# =========================================


def create_overlay(
    width, height, text, position, font_name, font_size, font_color, is_bold, is_italic
):

    overlay_buffer = BytesIO()

    c = canvas.Canvas(overlay_buffer, pagesize=(width, height))

    # -------------------------------------
    # FONT STYLE
    # -------------------------------------

    final_font = font_name

    if is_bold and is_italic:
        final_font = "Helvetica-BoldOblique"

    elif is_bold:
        final_font = "Helvetica-Bold"

    elif is_italic:
        final_font = "Helvetica-Oblique"

    else:
        final_font = "Helvetica"

    c.setFont(final_font, font_size)

    # -------------------------------------
    # FONT COLOR
    # -------------------------------------

    c.setFillColor(HexColor(font_color))

    # -------------------------------------
    # TEXT WIDTH
    # -------------------------------------

    text_width = c.stringWidth(text, final_font, font_size)

    # -------------------------------------
    # POSITION
    # -------------------------------------

    margin = 30

    x = margin
    y = margin

    if position == "top-left":

        x = margin
        y = height - margin

    elif position == "top-center":

        x = (width - text_width) / 2
        y = height - margin

    elif position == "top-right":

        x = width - text_width - margin
        y = height - margin

    elif position == "bottom-left":

        x = margin
        y = margin

    elif position == "bottom-center":

        x = (width - text_width) / 2
        y = margin

    elif position == "bottom-right":

        x = width - text_width - margin
        y = margin

    # -------------------------------------
    # DRAW TEXT
    # -------------------------------------

    c.drawString(x, y, text)

    c.save()

    overlay_buffer.seek(0)

    return overlay_buffer


# =========================================
# ADD PAGE NUMBER
# =========================================


@add_page_number_bp.route("/add_page_number", methods=["GET", "POST"])
def add_page_number():

    # =====================================
    # POST REQUEST
    # =====================================

    if request.method == "POST":

        # ---------------------------------
        # PDF FILE
        # ---------------------------------

        pdf_file = request.files.get("pdfs")

        if not pdf_file:
            return "No PDF uploaded"

        # ---------------------------------
        # FORM VALUES
        # ---------------------------------

        mode = request.form.get("mode")

        cover_page = True if request.form.get("cover_page") else False

        position = request.form.get("position")

        start_number = int(request.form.get("start_number", 1))

        page_format = request.form.get("page_format")

        font_family = request.form.get("font_family")

        font_color = request.form.get("font_color")

        is_bold = True if request.form.get("bold") else False

        is_italic = True if request.form.get("italic") else False

        is_underline = True if request.form.get("underline") else False

        # ---------------------------------
        # READ PDF
        # ---------------------------------

        pdf_reader = PdfReader(pdf_file)

        pdf_writer = PdfWriter()

        total_pages = len(pdf_reader.pages)

        current_number = start_number

        # ---------------------------------
        # PROCESS EACH PAGE
        # ---------------------------------

        for index, page in enumerate(pdf_reader.pages):

            actual_page = index + 1

            # skip cover page
            if cover_page and actual_page == 1:

                pdf_writer.add_page(page)

                continue

            # ---------------------------------
            # PAGE TEXT FORMAT
            # ---------------------------------

            if page_format == "number":

                page_text = f"{current_number}"

            elif page_format == "page-n":

                page_text = f"Page {current_number}"

            else:

                page_text = f"Page {current_number} " f"of {total_pages}"

            # ---------------------------------
            # PAGE SIZE
            # ---------------------------------

            width = float(page.mediabox.width)

            height = float(page.mediabox.height)

            # ---------------------------------
            # CREATE OVERLAY
            # ---------------------------------

            overlay_pdf = create_overlay(
                width=width,
                height=height,
                text=page_text,
                position=position,
                font_name=font_family,
                font_size=12,
                font_color=font_color,
                is_bold=is_bold,
                is_italic=is_italic,
            )

            overlay_reader = PdfReader(overlay_pdf)

            overlay_page = overlay_reader.pages[0]

            # ---------------------------------
            # MERGE OVERLAY
            # ---------------------------------

            page.merge_page(overlay_page)

            # underline
            # reportlab underline support
            # skipped for simplicity

            pdf_writer.add_page(page)

            current_number += 1

        # ---------------------------------
        # SAVE TO MEMORY
        # ---------------------------------

        output_buffer = BytesIO()

        pdf_writer.write(output_buffer)

        output_buffer.seek(0)

        # ---------------------------------
        # DOWNLOAD FILE
        # ---------------------------------

        output_filename = f"page_numbered_{pdf_file.filename}"

        return send_file(
            output_buffer,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/pdf",
        )

    # =====================================
    # GET REQUEST
    # =====================================

    return render_template("add_page_number.html")
