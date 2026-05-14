import inspect
import json
import os
import platform
import threading
import time
import traceback
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
)
from werkzeug.utils import secure_filename

from utils.file_utils import UPLOAD_FOLDER

# ==========================================
# WINDOWS ONLY CONFIG
# ==========================================

if platform.system() == "Windows":

    os.environ["PATH"] += os.pathsep + r"E:\sw"

# ==========================================
# IMPORT AFTER PATH CONFIG
# ==========================================

# Defer heavy PDF/OCR imports until worker execution to reduce memory at startup.

# ==========================================
# JOB HELPERS
# ==========================================


def get_job_folder(job_id):
    return os.path.join(UPLOAD_FOLDER, job_id)


def get_status_path(job_id):
    return os.path.join(get_job_folder(job_id), "status.json")


def save_job_status(job_id, status, message="", output_filename=None):
    os.makedirs(get_job_folder(job_id), exist_ok=True)
    status_data = {
        "status": status,
        "message": message,
        "output_filename": output_filename,
        "started_at": time.time(),
    }
    with open(get_status_path(job_id), "w", encoding="utf-8") as status_file:
        json.dump(status_data, status_file)


def load_job_status(job_id):
    status_path = get_status_path(job_id)
    if not os.path.exists(status_path):
        return None

    try:
        with open(status_path, "r", encoding="utf-8") as status_file:
            return json.load(status_file)
    except Exception:
        return None


def has_valid_table_data(table_collection):
    return any(
        not table.df.empty
        for page_tables in table_collection.values()
        for table in page_tables
    )


def build_extract_kwargs(ocr, pdf_obj, min_confidence=30):
    extract_kwargs = {
        "ocr": ocr,
        "min_confidence": min_confidence,
        "borderless_tables": True,
        "implicit_rows": True,
        "implicit_columns": True,
        "max_workers": 1,
    }
    return {
        key: value
        for key, value in extract_kwargs.items()
        if key in inspect.signature(pdf_obj.extract_tables).parameters
    }


def process_pdf_to_excel_job(job_id, pdf_path, sheet_mode):
    job_folder = get_job_folder(job_id)
    original_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_filename = f"{original_name}_converted_tables.xlsx"
    output_path = os.path.join(job_folder, output_filename)

    try:
        from img2table.document import PDF
        from img2table.ocr import TesseractOCR
        import pandas as pd

        ocr = TesseractOCR(n_threads=1, lang="eng", psm=6)
        pdf = PDF(src=pdf_path)

        tables = pdf.extract_tables(**build_extract_kwargs(ocr, pdf, min_confidence=30))

        if not tables or not has_valid_table_data(tables):
            tables = pdf.extract_tables(**build_extract_kwargs(ocr, pdf, min_confidence=20))

        if not tables or not has_valid_table_data(tables):
            save_job_status(job_id, "error", "No tables detected in PDF.")
            return

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            if sheet_mode == "separate":
                for page_number, page_tables in tables.items():
                    current_row = 0
                    sheet_name = f"Page_{page_number}"
                    wrote_any = False

                    for table in page_tables:
                        df = table.df
                        if df.empty:
                            continue

                        if current_row == 0:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            current_row = len(df) + 2
                        else:
                            df.to_excel(
                                writer,
                                sheet_name=sheet_name,
                                index=False,
                                startrow=current_row,
                            )
                            current_row += len(df) + 2

                        wrote_any = True

                    if not wrote_any:
                        continue
            else:
                current_row = 0
                valid_content_found = False

                for page_number, page_tables in tables.items():
                    page_has_tables = any(not table.df.empty for table in page_tables)
                    if not page_has_tables:
                        continue

                    valid_content_found = True
                    page_header = pd.DataFrame([[f"PAGE {page_number}"]])
                    page_header.to_excel(
                        writer,
                        sheet_name="All_Pages",
                        header=False,
                        index=False,
                        startrow=current_row,
                    )
                    current_row += 1

                    for table in page_tables:
                        df = table.df
                        if df.empty:
                            continue

                        df.to_excel(
                            writer,
                            sheet_name="All_Pages",
                            index=False,
                            startrow=current_row,
                        )
                        current_row += len(df) + 2

                if not valid_content_found:
                    save_job_status(job_id, "error", "No tables detected in PDF.")
                    return

        save_job_status(
            job_id, "complete", "Your Excel file is ready.", output_filename
        )
    except MemoryError as exc:
        print(f"PDF TO EXCEL JOB MEMORY ERROR [{job_id}]: {exc}")
        save_job_status(
            job_id,
            "error",
            "Server memory limit exceeded during conversion. Try a smaller PDF.",
        )
    except Exception as exc:
        print(f"PDF TO EXCEL JOB ERROR [{job_id}]: {exc}")
        traceback.print_exc()
        save_job_status(job_id, "error", "Conversion failed. Please try again.")


# ==========================================
# BLUEPRINT
# ==========================================

pdf_to_excel_bp = Blueprint("pdf_to_excel", __name__)

# ==========================================
# PAGE ROUTE
# ==========================================


@pdf_to_excel_bp.route("/pdf_to_excel")
def pdf_to_excel():

    return render_template("pdf_to_excel.html")


# ==========================================
# CONVERT PDF TO EXCEL
# ==========================================


@pdf_to_excel_bp.route("/convert_pdf_to_excel", methods=["POST"])
def convert_pdf_to_excel():
    uploaded_file = request.files.get("pdfs")

    if not uploaded_file:
        flash("Please upload a PDF file.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    filename = secure_filename(uploaded_file.filename or "")
    if not filename.lower().endswith(".pdf"):
        flash("Only PDF files are allowed.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    sheet_mode = request.form.get("sheet_mode", "single")

    job_id = str(uuid.uuid4())
    job_folder = get_job_folder(job_id)
    os.makedirs(job_folder, exist_ok=True)

    saved_pdf_path = os.path.join(job_folder, filename)
    uploaded_file.save(saved_pdf_path)

    save_job_status(job_id, "processing", "Conversion started")

    threading.Thread(
        target=process_pdf_to_excel_job,
        args=(job_id, saved_pdf_path, sheet_mode),
        daemon=True,
    ).start()

    return redirect(url_for("pdf_to_excel.pdf_to_excel_status", job_id=job_id))


@pdf_to_excel_bp.route("/pdf_to_excel/status/<job_id>")
def pdf_to_excel_status(job_id):
    status = load_job_status(job_id)
    if not status:
        flash("Invalid or expired conversion job.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    elapsed_time = int(time.time() - status.get("started_at", time.time()))

    return render_template(
        "pdf_to_excel_status.html",
        job_id=job_id,
        status=status["status"],
        message=status.get("message", ""),
        elapsed_time=elapsed_time,
    )


@pdf_to_excel_bp.route("/pdf_to_excel/download/<job_id>")
def download_pdf_to_excel(job_id):
    status = load_job_status(job_id)
    if not status:
        flash("Invalid or expired conversion job.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    if status["status"] != "complete":
        flash("Conversion is not ready yet.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel_status", job_id=job_id))

    output_filename = status.get("output_filename")
    if not output_filename:
        flash("Output file is unavailable.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    output_path = os.path.join(get_job_folder(job_id), output_filename)
    if not os.path.exists(output_path):
        flash("Converted file was not found.", "error")
        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_filename,
        mimetype=(
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        ),
    )
