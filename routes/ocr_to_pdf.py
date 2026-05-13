from flask import Blueprint, render_template, request, send_file
from io import BytesIO

import os
import tempfile
import zipfile
import platform

import ocrmypdf
import pytesseract


ocr_to_pdf_bp = Blueprint("ocr_to_pdf", __name__)


# WINDOWS TESSERACT PATH
if platform.system() == "Windows":

    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )


# SHOW PAGE
@ocr_to_pdf_bp.route("/ocr_to_pdf")
def ocr_to_pdf():
    return render_template("ocr_to_pdf.html")


# OCR PDF
@ocr_to_pdf_bp.route("/ocr_to_pdf", methods=["POST"])
def convert_ocr_to_pdf():

    uploaded_files = request.files.getlist("pdfs")

    if not uploaded_files:
        return "No PDF files uploaded"

    # Temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:

        generated_pdfs = []

        for uploaded_file in uploaded_files:

            try:

                # Save uploaded PDF
                input_pdf_path = os.path.join(
                    temp_dir,
                    uploaded_file.filename
                )

                uploaded_file.save(input_pdf_path)

                # Output OCR PDF
                output_pdf_name = (
                    os.path.splitext(uploaded_file.filename)[0]
                    + "_ocr.pdf"
                )

                output_pdf_path = os.path.join(
                    temp_dir,
                    output_pdf_name
                )

                # OCR PDF
                ocrmypdf.ocr(
                    input_pdf_path,
                    output_pdf_path,

                    # Languages
                    language="eng+hin+guj",

                    # Force OCR
                    force_ocr=True,

                    # Improve scan alignment
                    deskew=True,

                    # Basic optimization
                    optimize=1,
                )

                generated_pdfs.append(output_pdf_path)

            except Exception as e:

                return (
                    f"Error processing "
                    f"{uploaded_file.filename}: {str(e)}"
                )

        # SINGLE PDF DOWNLOAD
        if len(generated_pdfs) == 1:

            with open(generated_pdfs[0], "rb") as pdf_file:

                pdf_buffer = BytesIO(
                    pdf_file.read()
                )

            pdf_buffer.seek(0)

            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=os.path.basename(
                    generated_pdfs[0]
                ),
                mimetype="application/pdf",
            )

        # MULTIPLE PDFs -> ZIP
        else:

            zip_buffer = BytesIO()

            with zipfile.ZipFile(
                zip_buffer,
                "w",
                zipfile.ZIP_DEFLATED
            ) as zip_file:

                for pdf_path in generated_pdfs:

                    with open(pdf_path, "rb") as pdf_file:

                        zip_file.writestr(
                            os.path.basename(pdf_path),
                            pdf_file.read()
                        )

            zip_buffer.seek(0)

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name="ocr_to_pdfs.zip",
                mimetype="application/zip",
            )