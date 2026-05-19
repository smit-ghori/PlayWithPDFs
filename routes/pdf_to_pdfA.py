from flask import Blueprint, render_template, request, send_file
from io import BytesIO
import subprocess
import tempfile
import os
import platform
import pikepdf

pdf_to_pdfA_bp = Blueprint("pdf_to_pdfA", __name__)


@pdf_to_pdfA_bp.route("/pdf_to_pdfA", methods=["GET", "POST"])
def pdf_to_pdfA():

    if request.method == "POST":

        pdf_file = request.files.get("pdf_file")

        pdfa_version = request.form.get("pdfa_version", "2")

        pdf_password = request.form.get("pdf_password", "")

        if not pdf_file:
            return "No PDF uploaded"

        # CHECK PASSWORD AND DECRYPT BEFORE GHOSTSCRIPT CONVERSION
        try:

            pdf_bytes = pdf_file.read()

            input_bytes = pdf_bytes

            with pikepdf.open(BytesIO(pdf_bytes), password=pdf_password) as pdf:

                if pdf.is_encrypted:

                    decrypted_pdf = BytesIO()

                    pdf.save(decrypted_pdf)

                    input_bytes = decrypted_pdf.getvalue()

        except pikepdf.PasswordError:

            message = (
                "Incorrect password. Please try again."
                if pdf_password
                else "This PDF is password protected. Enter the password to convert it."
            )

            return {"status": "password_required", "message": message}

        # GHOSTSCRIPT PATH
        if platform.system() == "Windows":

            gs_command = r"C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe"

        else:

            gs_command = "gs"

        # TEMP FILES
        input_temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)

        output_temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)

        input_path = input_temp.name
        output_path = output_temp.name

        input_temp.close()
        output_temp.close()

        # SAVE PDF
        with open(input_path, "wb") as f:
            f.write(input_bytes)

        # PDF/A VERSION
        pdfa_flag = pdfa_version

        # COMMAND
        command = [
            gs_command,
            f"-dPDFA={pdfa_flag}",
            "-dBATCH",
            "-dNOPAUSE",
            "-dNOOUTERSAVE",
            "-sDEVICE=pdfwrite",
            "-sColorConversionStrategy=RGB",
            "-sProcessColorModel=DeviceRGB",
            "-dPDFACompatibilityPolicy=1",
            f"-sOutputFile={output_path}",
            input_path,
        ]

        # RUN

        try:

            subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        except FileNotFoundError:

            if os.path.exists(input_path):
                os.remove(input_path)

            if os.path.exists(output_path):
                os.remove(output_path)

            return (
                "Conversion Failed: Ghostscript was not found. "
                "Install Ghostscript or add gswin64c to PATH."
            ), 500

        except subprocess.CalledProcessError as e:

            if os.path.exists(input_path):
                os.remove(input_path)

            if os.path.exists(output_path):
                os.remove(output_path)

            return f"Conversion Failed : {e.stderr.decode()}"

        # READ OUTPUT

        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        # CLEANUP

        if os.path.exists(input_path):
            os.remove(input_path)

        if os.path.exists(output_path):
            os.remove(output_path)

        # SEND FILE

        return send_file(
            BytesIO(pdf_bytes),
            as_attachment=True,
            download_name="converted_pdfa.pdf",
            mimetype="application/pdf",
        )

    return render_template("pdf_to_pdfA.html")
