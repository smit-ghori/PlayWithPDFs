import os
from flask import Blueprint, send_file
from utils.file_utils import zip_folder

download_bp = Blueprint("download", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


@download_bp.route("/download/<folder_id>")
def download_file(folder_id):

    result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")

    if not os.path.exists(result_folder):
        return "Result not found", 404

    files = [
        f for f in os.listdir(result_folder)
        if f.endswith(".pdf") and os.path.getsize(os.path.join(result_folder, f)) > 0
    ]

    if not files:
        return "No valid output generated", 400

    # single file
    if len(files) == 1:
        file_path = os.path.join(result_folder, files[0])
        return send_file(file_path, as_attachment=True, download_name=files[0])

    # multiple files
    zip_path = os.path.join(UPLOAD_FOLDER, folder_id, "download.zip")

    if os.path.exists(zip_path):
        os.remove(zip_path)

    zip_folder(result_folder, zip_path)

    # verify zip created
    if not os.path.exists(zip_path):
        return "ZIP creation failed", 500

    if os.path.getsize(zip_path) == 0:
        return "ZIP file empty", 500

    return send_file(
        zip_path,
        as_attachment=True,
        mimetype="application/zip",
        download_name="compressed_pdfs.zip"
    )