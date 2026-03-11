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

    files = os.listdir(result_folder)

    if not files:
        return "No output generated", 400

    # if only one file → download directly
    if len(files) == 1:
        file_path = os.path.join(result_folder, files[0])
        return send_file(file_path, as_attachment=True)

    # if multiple files → zip them
    zip_path = os.path.join(UPLOAD_FOLDER, folder_id, "download.zip")

    if not os.path.exists(zip_path):
        zip_folder(result_folder, zip_path)

    return send_file(zip_path, as_attachment=True)