import os
import shutil
import zipfile
import subprocess
import tempfile
from io import BytesIO
from flask import Blueprint, render_template, request, send_file
from werkzeug.utils import secure_filename

word_to_pdf_bp = Blueprint("word_to_pdf", __name__)


def get_libreoffice_path():
    candidates = [
        os.environ.get("LIBREOFFICE_PATH"),
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        "/usr/lib/libreoffice/program/soffice",
        "/usr/bin/soffice",
    ]

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    raise RuntimeError(
        "LibreOffice not found. Install libreoffice and ensure 'soffice' is on PATH, or set LIBREOFFICE_PATH."
    )


def convert_docx_to_pdf(input_file, output_dir=None):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"No such file: {input_file}")

    if output_dir is None:
        output_dir = os.path.dirname(input_file)

    libreoffice_path = get_libreoffice_path()

    try:
        subprocess.run(
            [
                libreoffice_path,
                "--headless",
                "--convert-to",
                "pdf",
                input_file,
                "--outdir",
                output_dir,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"LibreOffice conversion failed: {e.stderr or e.stdout or str(e)}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to convert {input_file} to PDF: {e}") from e

    pdf_filename = os.path.splitext(os.path.basename(input_file))[0] + ".pdf"
    return os.path.join(output_dir, pdf_filename)


@word_to_pdf_bp.route("/word_to_pdf", methods=["GET", "POST"])
def word_to_pdf():
    if request.method == "POST":
        files = request.files.getlist("files")

        if not files:
            return "No files uploaded", 400

        allowed_extensions = {".docx"}
        for file in files:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                return (
                    f"Invalid file type: {file.filename}. Only .docx files are supported.",
                    400,
                )

        converted_files = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for file in files:
                filename = secure_filename(file.filename)
                if not filename:
                    return "Invalid file name", 400

                input_path = os.path.join(temp_dir, filename)
                file.save(input_path)

                pdf_path = convert_docx_to_pdf(input_path, temp_dir)
                converted_files.append((pdf_path, os.path.basename(pdf_path)))

            if len(converted_files) == 1:
                pdf_path, pdf_filename = converted_files[0]
                with open(pdf_path, "rb") as pdf_file:
                    pdf_stream = BytesIO(pdf_file.read())
                pdf_stream.seek(0)
                return send_file(
                    pdf_stream,
                    as_attachment=True,
                    download_name=pdf_filename,
                    mimetype="application/pdf",
                )

            zip_stream = BytesIO()
            with zipfile.ZipFile(zip_stream, "w", zipfile.ZIP_DEFLATED) as zipf:
                for pdf_path, pdf_filename in converted_files:
                    zipf.write(pdf_path, pdf_filename)

            zip_stream.seek(0)
            return send_file(
                zip_stream,
                as_attachment=True,
                download_name="converted_pdfs.zip",
                mimetype="application/zip",
            )

    return render_template("word_to_pdf.html")
