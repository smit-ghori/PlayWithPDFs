import os
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from pypdf import PdfWriter
from utils.file_utils import save_uploaded_files
from flask import send_file
from PIL import Image
from io import BytesIO

jpg_to_pdf_bp = Blueprint("jpg_to_pdf", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

@jpg_to_pdf_bp.route("/jpg_to_pdf", methods=["GET", "POST"])
def jpg_to_pdf():
    if request.method == "POST":
        files = request.files.getlist("images")
        order = request.form.get("image_order")

        order_list = list(map(int, order.split(",")))

        # 🔥 reorder safely
        file_map = {i: file for i, file in enumerate(files)}
        ordered_files = [file_map[i] for i in order_list]

        images = []

        for file in ordered_files:
            img = Image.open(file).convert("RGB")
            images.append(img)

        # 🔥 CREATE PDF IN MEMORY
        pdf_bytes = BytesIO()

        images[0].save(
            pdf_bytes,
            format="PDF",
            save_all=True,
            append_images=images[1:]
        )

        pdf_bytes.seek(0)  # move cursor to start

        return send_file(
            pdf_bytes,
            as_attachment=True,
            download_name="output.pdf",
            mimetype="application/pdf"
        )

    return render_template("jpg_to_pdf.html")