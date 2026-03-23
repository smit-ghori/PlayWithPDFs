import os
import platform
import subprocess
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files

repair_bp = Blueprint("repair", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


def repair_pdf(input_path, output_path):
    

    result = subprocess.run([
        # r"C:\Program Files (x86)\gs\gs10.07.0\bin\gswin32c",
        "gs",
        "-o", output_path,
        "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress",
        input_path
    ])

    if result.returncode != 0:
        raise RuntimeError("Ghostscript repair failed")

    if not os.path.exists(output_path):
        raise RuntimeError("Output PDF not created")

    if os.path.getsize(output_path) == 0:
        os.remove(output_path)
        raise RuntimeError("Repaired file is empty")


@repair_bp.route("/repair", methods=["GET", "POST"])
def repair():
    if request.method == "POST":
        files = request.files.getlist("pdfs")

        if not files:
            return "No files uploaded", 400

        folder_id, saved_files = save_uploaded_files(files)

        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        successful_files = []

        for pdf in saved_files:
            filename = os.path.basename(pdf)
            output_path = os.path.join(result_folder, filename)            

            try:
                repair_pdf(pdf, output_path)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    successful_files.append(output_path)

            except Exception as e:
                print("Repair failed:", filename, e)

        if not successful_files:
            return "Repair failed for all files", 500

        return redirect(url_for("download.download_file", folder_id=folder_id))

    return render_template("repair.html")