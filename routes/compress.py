import os
import subprocess
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files

compress_bp = Blueprint("compress", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


def compress_pdf(input_path, output_path, quality="screen"):

    # gs_path = "C:\\Program Files (x86)\\gs\gs10.07.0\\bin\\gswin32"  # ✅ Linux compatible

    gs_path = "gs"
    result = subprocess.run([
        gs_path,
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS=/{quality}",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ])

    if result.returncode != 0:
        raise RuntimeError("Ghostscript compression failed")

    if not os.path.exists(output_path):
        raise RuntimeError("Output PDF not created")

    if os.path.getsize(output_path) == 0:
        os.remove(output_path)
        raise RuntimeError("Compressed file is empty")


@compress_bp.route("/compress", methods=["GET", "POST"])
def compress():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        if not files:
            return "No files uploaded", 400

        folder_id, saved_files = save_uploaded_files(files)

        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        compression_type = request.form.get("compression", "recommended")

        quality_map = {
            "extreme": "screen",
            "recommended": "ebook",
            "low": "printer"
        }

        quality = quality_map.get(compression_type, "ebook")

        successful_files = []

        for pdf in saved_files:

            filename = os.path.basename(pdf)
            output_path = os.path.join(result_folder, filename)

            try:
                compress_pdf(pdf, output_path, quality)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    successful_files.append(output_path)

            except Exception as e:
                print("Compression failed:", filename, e)

        if not successful_files:
            return "Compression failed for all files", 500

        return redirect(url_for("download.download_file", folder_id=folder_id))

    return render_template("compress.html")