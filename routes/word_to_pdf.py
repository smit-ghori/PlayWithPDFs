import os
import zipfile
import subprocess
import platform
import shutil
from io import BytesIO
from flask import Blueprint, render_template, request, send_file

word_to_pdf_bp = Blueprint("word_to_pdf", __name__)


def convert_word_to_pdf_windows(input_path, pdf_path):
    """
    Convert using Windows COM (Microsoft Word).
    """
    try:
        import win32com.client

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(input_path))
        doc.SaveAs2(os.path.abspath(pdf_path), FileFormat=17)
        doc.Close()
        word.Quit()
        return True
    except Exception as e:
        print(f"Windows COM conversion failed: {e}")
        return False


def convert_word_to_pdf_libreoffice(input_path, pdf_path, temp_dir):
    """
    Convert using LibreOffice (works on Linux and Windows).
    """
    try:
        soffice_path = None

        if platform.system() == "Windows":
            candidates = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            soffice_path = next((path for path in candidates if os.path.exists(path)), None)
        else:
            candidates = [
                shutil.which("libreoffice"),
                shutil.which("soffice"),
                "/usr/bin/libreoffice",
                "/usr/bin/soffice",
            ]
            soffice_path = next((path for path in candidates if path and os.path.exists(path)), None)

        if not soffice_path:
            raise FileNotFoundError(
                "LibreOffice executable not found. Checked: libreoffice, soffice"
            )

        subprocess.run(
            [
                soffice_path,
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--invisible",
                "--norestore",
                "--convert-to",
                "pdf:writer_pdf_Export",
                "--outdir",
                temp_dir,
                input_path,
            ],
            check=True,
            timeout=120,
        )

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Expected output PDF was not created: {pdf_path}")

        return True
    except Exception as e:
        print(f"LibreOffice conversion failed: {e}")
        return False


def convert_word_to_pdf(input_stream, filename):
    """
    Convert a Word file to PDF using the best available method.
    On Windows: tries Windows COM first, then LibreOffice
    On Linux: uses LibreOffice
    Returns BytesIO containing the PDF.
    """
    temp_dir = os.path.abspath("temp_convert")
    os.makedirs(temp_dir, exist_ok=True)

    input_path = os.path.join(temp_dir, filename)
    with open(input_path, "wb") as f:
        f.write(input_stream.read())

    pdf_filename = os.path.splitext(filename)[0] + ".pdf"
    pdf_path = os.path.join(temp_dir, pdf_filename)

    # Try appropriate conversion method
    success = False
    if platform.system() == "Windows":
        # Try Windows COM first
        success = convert_word_to_pdf_windows(input_path, pdf_path)

    # Fallback to LibreOffice
    if not success:
        success = convert_word_to_pdf_libreoffice(input_path, pdf_path, temp_dir)

    if not success:
        raise Exception(
            f"Failed to convert {filename} to PDF. "
            "Make sure LibreOffice is installed and available on the server."
        )

    # Read back the PDF
    pdf_stream = BytesIO()
    with open(pdf_path, "rb") as f:
        pdf_stream.write(f.read())
    pdf_stream.seek(0)

    # Clean up temp files
    if os.path.exists(input_path):
        os.remove(input_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    return pdf_stream, pdf_filename


@word_to_pdf_bp.route("/word_to_pdf", methods=["GET", "POST"])
def word_to_pdf():
    if request.method == "POST":
        files = request.files.getlist("files")

        if not files:
            return "No files uploaded", 400

        # Case 1: Single file → return PDF directly
        if len(files) == 1:
            file = files[0]
            pdf_stream, pdf_filename = convert_word_to_pdf(file.stream, file.filename)
            return send_file(
                pdf_stream,
                as_attachment=True,
                download_name=pdf_filename,
                mimetype="application/pdf",
            )

        # Case 2: Multiple files → return ZIP of PDFs
        else:
            zip_stream = BytesIO()
            with zipfile.ZipFile(zip_stream, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    pdf_stream, pdf_filename = convert_word_to_pdf(
                        file.stream, file.filename
                    )
                    zipf.writestr(pdf_filename, pdf_stream.read())

            zip_stream.seek(0)
            return send_file(
                zip_stream,
                as_attachment=True,
                download_name="converted_pdfs.zip",
                mimetype="application/zip",
            )

    return render_template("word_to_pdf.html")
