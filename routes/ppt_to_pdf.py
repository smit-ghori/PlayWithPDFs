from flask import Blueprint, render_template, request, send_file
from io import BytesIO

import os
import subprocess
import tempfile
import platform
import zipfile

ppt_to_pdf_bp = Blueprint("ppt_to_pdf", __name__)


# SHOW PAGE
@ppt_to_pdf_bp.route("/ppt_to_pdf")
def ppt_to_pdf():
    return render_template("ppt_to_pdf.html")


# CONVERT PPT TO PDF
@ppt_to_pdf_bp.route("/ppt_to_pdf", methods=["POST"])
def convert_ppt_to_pdf():

    uploaded_files = request.files.getlist("ppts")

    if not uploaded_files:
        return "No PowerPoint files uploaded"

    # LibreOffice path
    if platform.system() == "Windows":
        libreoffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    else:
        libreoffice_path = "libreoffice"

    # Temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:

        generated_pdfs = []

        for uploaded_file in uploaded_files:

            try:

                # Save uploaded PPT/PPTX file
                input_path = os.path.join(temp_dir, uploaded_file.filename)

                uploaded_file.save(input_path)

                # LibreOffice conversion command
                command = [
                    libreoffice_path,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    input_path,
                    "--outdir",
                    temp_dir,
                ]

                # Run conversion
                subprocess.run(command, check=True)

                # Output PDF filename
                pdf_filename = os.path.splitext(uploaded_file.filename)[0] + ".pdf"

                pdf_path = os.path.join(temp_dir, pdf_filename)

                generated_pdfs.append(pdf_path)

            except Exception as e:
                return f"Error converting {uploaded_file.filename}: {str(e)}"

        # SINGLE PDF DOWNLOAD
        if len(generated_pdfs) == 1:

            with open(generated_pdfs[0], "rb") as pdf_file:

                pdf_buffer = BytesIO(pdf_file.read())

            pdf_buffer.seek(0)

            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=os.path.basename(generated_pdfs[0]),
                mimetype="application/pdf",
            )

        # MULTIPLE PDFS -> ZIP DOWNLOAD
        else:

            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

                for pdf_path in generated_pdfs:

                    zip_file.write(pdf_path, arcname=os.path.basename(pdf_path))

            zip_buffer.seek(0)

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name="converted_pdfs.zip",
                mimetype="application/zip",
            )
