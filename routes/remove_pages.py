import os
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files

remove_pages_bp = Blueprint("remove_pages", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

@remove_pages_bp.route("/remove_pages", methods=["GET", "POST"])
def remove_pages():
    return render_template("remove_pages.html")