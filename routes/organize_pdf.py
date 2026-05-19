from flask import Blueprint, render_template, request, send_file

from io import BytesIO

import json

from pypdf import PdfReader, PdfWriter

organize_pdf_bp = Blueprint("organize_pdf", __name__)


# ORGANIZE PDF


@organize_pdf_bp.route("/organize_pdf", methods=["GET", "POST"])
def organize_pdf():

    # GET REQUEST

    if request.method == "GET":

        return render_template("organize_pdf.html")

    # POST REQUEST

    try:

        # Uploaded PDF
        pdf_file = request.files.get("pdf")

        if not pdf_file:

            return "No PDF uploaded", 400

        # Page order from frontend
        page_order = request.form.get("page_order")

        if not page_order:

            return "No page order received", 400

        # Convert JSON string to Python list
        page_order = json.loads(page_order)

        # READ PDF

        reader = PdfReader(pdf_file)

        writer = PdfWriter()

        # REORDER PAGES

        for index in page_order:

            writer.add_page(reader.pages[index])

        # STORE PDF IN MEMORY

        output_pdf = BytesIO()

        writer.write(output_pdf)

        output_pdf.seek(0)

        # SEND FILE

        return send_file(
            output_pdf,
            as_attachment=True,
            download_name="organized.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:

        return f"Error: {str(e)}", 500
