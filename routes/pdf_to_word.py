from flask import Blueprint, render_template, request, send_file
from io import BytesIO

from pdf2docx import Converter

import os
import tempfile
import zipfile

pdf_to_word_bp = Blueprint("pdf_to_word", __name__)


# SHOW PAGE
@pdf_to_word_bp.route("/pdf_to_word")
def pdf_to_word():
    return render_template("pdf_to_word.html")


# CONVERT PDF TO WORD
@pdf_to_word_bp.route("/pdf_to_word", methods=["POST"])
def convert_pdf_to_word():

    uploaded_files = request.files.getlist("pdfs")

    if not uploaded_files:
        return "No PDF files uploaded"

    # Temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:

        generated_docs = []

        for uploaded_file in uploaded_files:

            try:

                # Save uploaded PDF
                pdf_path = os.path.join(temp_dir, uploaded_file.filename)

                uploaded_file.save(pdf_path)

                # Output DOCX filename
                docx_filename = os.path.splitext(uploaded_file.filename)[0] + ".docx"

                docx_path = os.path.join(temp_dir, docx_filename)

                # Convert PDF -> DOCX
                cv = Converter(pdf_path)

                cv.convert(docx_path)

                cv.close()

                generated_docs.append(docx_path)

            except Exception as e:
                return f"Error converting {uploaded_file.filename}: {str(e)}"

        # SINGLE DOCX DOWNLOAD
        if len(generated_docs) == 1:

            with open(generated_docs[0], "rb") as doc_file:

                doc_buffer = BytesIO(doc_file.read())

            doc_buffer.seek(0)

            return send_file(
                doc_buffer,
                as_attachment=True,
                download_name=os.path.basename(generated_docs[0]),
                mimetype="application/octet-stream",
            )

        # MULTIPLE DOCX -> ZIP DOWNLOAD
        else:

            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

                for doc_path in generated_docs:

                    with open(doc_path, "rb") as doc_file:

                        zip_file.writestr(os.path.basename(doc_path), doc_file.read())

            zip_buffer.seek(0)

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name="converted_docs.zip",
                mimetype="application/zip",
            )
