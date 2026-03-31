import os
from io import BytesIO
from flask import Blueprint, render_template, request, send_file
from PIL import Image

jpg_to_pdf_bp = Blueprint("jpg_to_pdf", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


def prepare_image_for_pdf(img, margin):
    # A4 size in pixels (approx at 72 DPI)
    A4_WIDTH = 595
    A4_HEIGHT = 842

    # margin sizes
    if margin == "none":
        m = 0
    elif margin == "small":
        m = 20
    else:
        m = 50

    # available area
    max_width = A4_WIDTH - 2 * m
    max_height = A4_HEIGHT - 2 * m

    # resize image (keep aspect ratio)
    img.thumbnail((max_width, max_height))

    # create A4 canvas
    new_img = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")

    # center image
    x = (A4_WIDTH - img.width) // 2
    y = (A4_HEIGHT - img.height) // 2

    new_img.paste(img, (x, y))

    return new_img


def add_margin(img, margin):
    if margin == "none":
        return img

    size = 20 if margin == "small" else 50

    new_img = Image.new("RGB", (img.width + size * 2, img.height + size * 2), "white")

    new_img.paste(img, (size, size))
    return new_img


def merge_all(ordered_files, margin):
    images = []

    for file in ordered_files:
        img = Image.open(file).convert("RGB")
        img = add_margin(img, margin)
        images.append(img)

    pdf_bytes = BytesIO()

    images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images[1:])

    pdf_bytes.seek(0)

    return send_file(
        pdf_bytes,
        as_attachment=True,
        download_name="PlayWithPdfs_output.pdf",
        mimetype="application/pdf",
    )


import zipfile


def all_in_zip(ordered_files, margin):
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zf:

        for i, file in enumerate(ordered_files):
            img = Image.open(file).convert("RGB")
            img = prepare_image_for_pdf(img, margin)

            pdf_bytes = BytesIO()
            img.save(pdf_bytes, format="PDF")
            pdf_bytes.seek(0)

            # 🔥 add to zip
            zf.writestr(f"image_{i+1}.pdf", pdf_bytes.read())

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name="PlayWithPdfs_images.zip",
        mimetype="application/zip",
    )


@jpg_to_pdf_bp.route("/jpg_to_pdf", methods=["GET", "POST"])
def jpg_to_pdf():
    if request.method == "POST":
        files = request.files.getlist("images")
        if not files:
            return "No images uploaded", 400

        order = request.form.get("image_order", "").strip()
        ordered_files = files

        if order:
            try:
                order_list = [int(i) for i in order.split(",") if i.strip()]
                reordered = [files[i] for i in order_list if 0 <= i < len(files)]
                if reordered:
                    ordered_files = reordered
            except ValueError:
                ordered_files = files

        margin = request.form.get("margin", "none")
        merge = request.form.get("merge")

        if merge == "on":
            return merge_all(ordered_files, margin)
        return all_in_zip(ordered_files, margin)

    return render_template("jpg_to_pdf.html")
