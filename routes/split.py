import os
from flask import Blueprint, render_template, request, redirect, url_for
from pypdf import PdfWriter, PdfReader
from utils.file_utils import save_uploaded_files

split_bp = Blueprint("split", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


def split_pdf_by_range(input_pdf_path, output_pdf_path, start_page, end_page):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page_num in range(start_page - 1, end_page):
        if page_num < len(reader.pages):
            writer.add_page(reader.pages[page_num])
        else:
            break

    with open(output_pdf_path, 'wb') as output_stream:
        writer.write(output_stream)


def split_pdf_by_size(input_pdf_path, result_folder, max_size_mb):
    reader = PdfReader(input_pdf_path)

    max_size_bytes = max_size_mb * 1024 * 1024

    part = 1
    writer = PdfWriter()

    temp_path = os.path.join(result_folder, "temp_check.pdf")  # ✅ single temp file

    for page in reader.pages:
        writer.add_page(page)

        # Write temp file to check size
        with open(temp_path, "wb") as f:
            writer.write(f)

        current_size = os.path.getsize(temp_path)

        # 🚨 If size exceeded
        if current_size > max_size_bytes:
            # Remove last added page by restarting writer
            # Save previous valid part first

            writer = PdfWriter()  # reset writer
            writer.add_page(page)  # start new part with current page

            part += 1

        # Save current part
        output_path = os.path.join(result_folder, f"part_{part}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

    # 🧹 Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)


@split_bp.route("/split", methods=["GET", "POST"])
def split():

    if request.method == "POST":
        files = request.files.getlist("pdfs")

        if not files or files[0].filename == "":
            return "No file uploaded"

        folder_id, saved_file = save_uploaded_files(files)

        # ✅ Handle both cases (string OR list)
        if isinstance(saved_file, list):
            saved_file_path = saved_file[0]
        else:
            saved_file_path = saved_file

        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        split_type = request.form.get("splitType")

        if split_type == "range":
            start_page = int(request.form.get("start_page"))
            end_page = int(request.form.get("end_page"))

            output_file_path = os.path.join(result_folder, "split_range.pdf")

            split_pdf_by_range(
                saved_file_path,
                output_file_path,
                start_page,
                end_page
            )
            return redirect(url_for("download.download_file", folder_id=folder_id))
        
        elif split_type == "size":
            max_size = request.form.get("max_size")

            if not max_size:
                return "Please enter max size"

            max_size = int(max_size)

            split_pdf_by_size(
                saved_file_path,
                result_folder,
                max_size
            )
            return redirect(url_for("download.download_file", folder_id=folder_id))


    return render_template("split.html")