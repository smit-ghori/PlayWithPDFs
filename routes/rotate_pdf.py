from flask import Blueprint, render_template, request, send_file

from io import BytesIO
import json

from PyPDF2 import PdfReader, PdfWriter

rotate_pdf_bp = Blueprint("rotate_pdf", __name__)


@rotate_pdf_bp.route("/rotate_pdf")
def rotate_pdf():
    return render_template("rotate_pdf.html")


@rotate_pdf_bp.route("/rotate_pdf", methods=["POST"])
def rotate_pdf_file():


    uploaded_file = request.files.get("pdfs")

    if not uploaded_file:
        return "No PDF uploaded"

    # GET ROTATION DATA
    rotation_data = request.form.get("rotation_data")

    if not rotation_data:
        return "No rotation data found"

    # JSON -> Python Dictionary
    rotation_data = json.loads(rotation_data)

    try:

        # READ PDF
        pdf_reader = PdfReader(uploaded_file)

        pdf_writer = PdfWriter()

        # ROTATE PAGES
        for index, page in enumerate(pdf_reader.pages):

            page_number = str(index + 1)

            rotation_angle = int(rotation_data.get(page_number, 0))

            # Normalize angle
            rotation_angle = rotation_angle % 360

            # Rotate page
            if rotation_angle != 0:
                page.rotate(rotation_angle)

            pdf_writer.add_page(page)

        # STORE PDF IN MEMORY

        pdf_buffer = BytesIO()

        pdf_writer.write(pdf_buffer)

        pdf_buffer.seek(0)

        # DOWNLOAD FILE
        original_name = uploaded_file.filename

        output_filename = f"rotated_{original_name}"

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/pdf",
        )

    except Exception as e:

        return f"Error rotating PDF: {str(e)}"
