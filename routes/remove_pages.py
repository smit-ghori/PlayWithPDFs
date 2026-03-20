import os
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files
from pypdf import PdfReader, PdfWriter

remove_pages_bp = Blueprint("remove_pages", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


@remove_pages_bp.route("/remove_pages", methods=["GET", "POST"])
def remove_pages():
    if request.method == "POST":

        # 📌 1. Get uploaded file
        file = request.files.get("pdfs")

        if not file:
            return "No file uploaded", 400

        # 📌 2. Get selected pages (comma-separated string)
        pages_to_remove = request.form.get("pages_to_remove", "")

        print("RAW pages_to_remove:", pages_to_remove)

        # ✅ Convert "1,2,3" → [1,2,3]
        pages_list = [int(p) for p in pages_to_remove.split(",") if p]
        pages_set = set(pages_list)

        print("Parsed pages:", pages_set)

        # 📌 3. Save uploaded file
        folder_id, saved_files = save_uploaded_files([file])
        saved_file_path = saved_files[0]

        # 📌 4. Create result folder
        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        output_file_path = os.path.join(result_folder, "removed_pages.pdf")

        # 📌 5. Read PDF
        reader = PdfReader(saved_file_path)
        writer = PdfWriter()

        total_pages = len(reader.pages)
        print("Total pages in PDF:", total_pages)

        # 🚨 Safety check (optional but good)
        if len(pages_set) >= total_pages:
            return "Cannot remove all pages", 400

        # 📌 6. Remove selected pages
        for i, page in enumerate(reader.pages, start=1):  # 1-based index
            if i not in pages_set:
                writer.add_page(page)

        # 📌 7. Save output PDF
        with open(output_file_path, "wb") as f:
            writer.write(f)

        print("Removed pages:", pages_set)
        print("Saved to:", output_file_path)

        # 📌 8. Redirect to download
        return redirect(url_for("download.download_file", folder_id=folder_id))

    return render_template("remove_pages.html")