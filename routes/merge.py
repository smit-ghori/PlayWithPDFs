import os
from flask import Blueprint, render_template, request, redirect, url_for
from pypdf import PdfWriter
from utils.file_utils import save_uploaded_files

merge_bp = Blueprint("merge", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

@merge_bp.route("/merge", methods=["GET", "POST"])
def merge():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        if not files:
            return "No files uploaded", 400

        folder_id, saved_files = save_uploaded_files(files)

        writer = PdfWriter()

        for pdf in saved_files:
            writer.append(pdf)

        # result folder
        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        output_path = os.path.join(result_folder, "merged.pdf")

        writer.write(output_path)
        writer.close()

        return redirect(url_for("download.download_file", folder_id=folder_id))

    return render_template("merge.html")