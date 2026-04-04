from flask import Blueprint, render_template, request, send_file
import zipfile
from io import BytesIO
import fitz  # PyMuPDF

pdf_to_jpg_bp = Blueprint("pdf_to_jpg", __name__)


@pdf_to_jpg_bp.route("/pdf_to_jpg", methods=["GET", "POST"])
def pdf_to_jpg():
    if request.method == "POST":
        files = request.files.getlist("pdfs")

        # Create ZIP in memory
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_index, pdf_file in enumerate(files):
                pdf_bytes = pdf_file.read()

                # Open PDF from memory
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                for page_index, page in enumerate(doc):
                    # Convert page to image
                    pix = page.get_pixmap()

                    # Save image to memory
                    img_buffer = BytesIO(pix.tobytes("jpeg"))

                    # File name inside zip
                    filename = f"file{file_index+1}_page{page_index+1}.jpg"

                    # Add to ZIP
                    zip_file.writestr(filename, img_buffer.getvalue())

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="converted_images.zip",
        )

    return render_template("pdf_to_jpg.html")
