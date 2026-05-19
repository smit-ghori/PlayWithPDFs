import os
import zipfile
import shutil
import platform
import tempfile
import subprocess

from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
)

compress_bp = Blueprint("compress", __name__)


# =====================================================
# GET GHOSTSCRIPT PATH
# =====================================================


def get_gs_path():

    # WINDOWS
    if platform.system() == "Windows":

        gs = shutil.which("gswin64c")

        if gs:
            return gs

        gs = shutil.which("gswin32c")

        if gs:
            return gs

        possible_paths = [
            r"C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe",
            r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe",
            r"C:\Program Files (x86)\gs\gs10.07.0\bin\gswin32c.exe",
            r"C:\Program Files (x86)\gs\gs10.06.0\bin\gswin32c.exe",
        ]

        for path in possible_paths:

            if os.path.exists(path):
                return path

        raise Exception("Ghostscript not found")

    # RENDER / LINUX
    return "gs"


# =====================================================
# COMPRESS SINGLE PDF
# =====================================================


def compress_pdf(file, quality="ebook"):

    gs_path = get_gs_path()

    # -----------------------------------------
    # INPUT TEMP FILE
    # -----------------------------------------

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as input_temp:

        input_temp.write(file.read())

        input_path = input_temp.name

    # -----------------------------------------
    # OUTPUT TEMP FILE
    # -----------------------------------------

    output_temp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)

    output_path = output_temp.name

    output_temp.close()

    # -----------------------------------------
    # GHOSTSCRIPT COMMAND
    # -----------------------------------------

    command = [
        gs_path,
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS=/{quality}",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path,
    ]

    result = subprocess.run(command)

    # -----------------------------------------
    # ERROR CHECK
    # -----------------------------------------

    if result.returncode != 0:

        os.remove(input_path)

        if os.path.exists(output_path):
            os.remove(output_path)

        raise RuntimeError("Ghostscript compression failed")

    # -----------------------------------------
    # READ COMPRESSED PDF
    # -----------------------------------------

    with open(output_path, "rb") as f:

        compressed_data = f.read()

    # -----------------------------------------
    # CLEANUP
    # -----------------------------------------

    os.remove(input_path)
    os.remove(output_path)

    return compressed_data


# =====================================================
# COMPRESS ROUTE
# =====================================================


@compress_bp.route("/compress", methods=["GET", "POST"])
def compress():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        if not files:
            return "No PDF uploaded", 400

        # -----------------------------------------
        # QUALITY
        # -----------------------------------------

        compression_type = request.form.get("compression", "recommended")

        quality_map = {
            "extreme": "screen",
            "recommended": "ebook",
            "low": "printer",
        }

        quality = quality_map.get(compression_type, "ebook")

        # =====================================================
        # SINGLE FILE
        # =====================================================

        if len(files) == 1:

            pdf = files[0]

            try:

                compressed_pdf = compress_pdf(pdf, quality)

                return send_file(
                    BytesIO(compressed_pdf),
                    as_attachment=True,
                    download_name=f"compressed_{pdf.filename}",
                    mimetype="application/pdf",
                )

            except Exception as e:

                return f"Compression failed: {str(e)}", 500

        # =====================================================
        # MULTIPLE FILES -> ZIP
        # =====================================================

        zip_buffer = BytesIO()

        try:

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

                for pdf in files:

                    try:

                        compressed_pdf = compress_pdf(pdf, quality)

                        compressed_name = f"compressed_{pdf.filename}"

                        zip_file.writestr(compressed_name, compressed_pdf)

                    except Exception as e:

                        print(f"Failed: {pdf.filename}", str(e))

            zip_buffer.seek(0)

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name="compressed_pdfs.zip",
                mimetype="application/zip",
            )

        except Exception as e:

            return f"ZIP creation failed: {str(e)}", 500

    return render_template("compress.html")
