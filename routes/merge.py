import os
from io import BytesIO
from flask import Blueprint, render_template, request, send_file
from pypdf import PdfWriter, PdfReader

merge_bp = Blueprint("merge", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


@merge_bp.route("/merge", methods=["GET", "POST"])
def merge():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        # Check if files are uploaded
        if not files or files[0].filename == "":
            return render_template("merge.html", error="Please upload PDF files.")

        merger = PdfWriter()

        try:

            # Merge all uploaded PDFs
            for file in files:

                pdf = PdfReader(file)

                for page in pdf.pages:
                    merger.add_page(page)

            # Store merged PDF in memory
            pdf_buffer = BytesIO()

            merger.write(pdf_buffer)
            merger.close()

            pdf_buffer.seek(0)

            # Send merged PDF directly
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name="merged.pdf",
                mimetype="application/pdf",
            )

        except Exception as e:
            return render_template(
                "merge.html", error=f"Error while merging PDFs: {str(e)}"
            )

    return render_template("merge.html")
