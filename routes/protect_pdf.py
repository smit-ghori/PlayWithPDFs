from flask import Blueprint, render_template, request, send_file
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter

protect_pdf_bp = Blueprint("protect_pdf", __name__)


@protect_pdf_bp.route("/protect_pdf", methods=["GET", "POST"])
def protect_pdf():

    if request.method == "POST":
        pdf_file = request.files.get("pdfs")
        password = request.form.get("pdf_password")

        # VALIDATION
        if not pdf_file:
            return "Please upload PDF file"

        if not password:
            return "Please enter password"

        try:

            # READ PDF
            reader = PdfReader(pdf_file)

            writer = PdfWriter()

            # ADD ALL PAGES
            for page in reader.pages:
                writer.add_page(page)

            # ADD PASSWORD
            writer.encrypt(password)

            # STORE TEMP PDF IN MEMORY
            pdf_stream = BytesIO()

            writer.write(pdf_stream)

            pdf_stream.seek(0)

            return send_file(
                pdf_stream,
                as_attachment=True,
                download_name="protected_PlayWithPDFs.pdf",
                mimetype="application/pdf",
            )

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("protect_pdf.html")
