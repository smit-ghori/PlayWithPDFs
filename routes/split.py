import os
from flask import Blueprint, render_template, request, redirect, url_for
from pypdf import PdfWriter
from utils.file_utils import save_uploaded_files

split_bp = Blueprint("split", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


@split_bp.route("/split", methods=["GET", "POST"])
def split():
    print("🔥 ROUTE HIT:", request.method, flush=True)

    if request.method == "POST":
        print("✅ FORM SUBMITTED", flush=True)

    return render_template("split.html")