import os
from io import BytesIO
from flask import Blueprint, render_template, request, send_file

word_to_pdf_bp = Blueprint("word_to_pdf", __name__)


@word_to_pdf_bp.route("/word_to_pdf", methods=["GET", "POST"])
def word_to_pdf():
    if request.method == "POST":
        files = request.files.getlist("files")
        print(files)
    return render_template("word_to_pdf.html")
