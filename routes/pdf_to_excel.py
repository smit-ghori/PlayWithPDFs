import os
import io
import tempfile
import platform
import pandas as pd

from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
)

# ==========================================
# WINDOWS ONLY CONFIG
# ==========================================

if platform.system() == "Windows":

    os.environ["PATH"] += os.pathsep + r"E:\sw"

# ==========================================
# IMPORT AFTER PATH CONFIG
# ==========================================

from img2table.document import PDF
from img2table.ocr import TesseractOCR

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

    temp_pdf_path = None

    try:

        # ==========================================
        # GET FILE
        # ==========================================

        uploaded_file = request.files.get("pdfs")

        if not uploaded_file:

            flash("Please upload a PDF file.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        # ==========================================
        # VALIDATE FILE TYPE
        # ==========================================

        filename = uploaded_file.filename.lower()

        if not filename.endswith(".pdf"):

            flash("Only PDF files are allowed.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        # ==========================================
        # GET EXPORT MODE
        # ==========================================

        sheet_mode = request.form.get("sheet_mode", "single")

        separate_page_sheets = sheet_mode == "separate"

        # ==========================================
        # READ FILE BYTES
        # ==========================================

        pdf_bytes = uploaded_file.read()

        if not pdf_bytes:

            flash("Uploaded PDF is empty.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        # ==========================================
        # CREATE TEMP FILE
        # ==========================================

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        temp_file.write(pdf_bytes)

        temp_file.close()

        temp_pdf_path = temp_file.name

        # ==========================================
        # INITIALIZE OCR
        # ==========================================

        ocr = TesseractOCR(n_threads=1, lang="eng", psm=6)

        # ==========================================
        # LOAD PDF
        # ==========================================

        pdf = PDF(src=temp_pdf_path)

        # ==========================================
        # EXTRACT TABLES
        # ==========================================

        tables = pdf.extract_tables(
            ocr=ocr,
            min_confidence=50,
        )

        # ==========================================
        # NO TABLE FOUND
        # ==========================================

        if not tables:

            flash("No tables detected in PDF.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        # ==========================================
        # CREATE EXCEL BUFFER
        # ==========================================

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:

            # ==========================================
            # MODE 1:
            # EACH PAGE IN SEPARATE SHEET
            # ==========================================

            if separate_page_sheets:

                for page_number, page_tables in tables.items():

                    combined_df = pd.DataFrame()

                    for table in page_tables:

                        df = table.df

                        if df.empty:
                            continue

                        combined_df = pd.concat([combined_df, df], ignore_index=True)

                        # Empty Row
                        empty_row = pd.DataFrame(
                            [[""] * len(df.columns)], columns=df.columns
                        )

                        combined_df = pd.concat(
                            [combined_df, empty_row], ignore_index=True
                        )

                    # Skip empty pages
                    if combined_df.empty:
                        continue

                    combined_df.to_excel(
                        writer, sheet_name=f"Page_{page_number}", index=False
                    )

            # ==========================================
            # MODE 2:
            # ALL PAGES IN SINGLE SHEET
            # ==========================================

            else:

                final_df = pd.DataFrame()

                for page_number, page_tables in tables.items():

                    # Page Header
                    page_title = pd.DataFrame(
                        [[f"PAGE {page_number}"]], columns=["Page"]
                    )

                    final_df = pd.concat([final_df, page_title], ignore_index=True)

                    for table in page_tables:

                        df = table.df

                        if df.empty:
                            continue

                        final_df = pd.concat([final_df, df], ignore_index=True)

                        # Empty Row
                        empty_row = pd.DataFrame(
                            [[""] * len(df.columns)], columns=df.columns
                        )

                        final_df = pd.concat([final_df, empty_row], ignore_index=True)

                # Save final sheet
                final_df.to_excel(writer, sheet_name="All_Pages", index=False)

        # ==========================================
        # RESET BUFFER POINTER
        # ==========================================

        excel_buffer.seek(0)

        # ==========================================
        # RETURN FILE
        # ==========================================

        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name="converted_tables.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
            ),
        )

    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except Exception as e:

        print(f"PDF TO EXCEL ERROR: {str(e)}")

        flash("Failed to convert PDF to Excel.", "error")

        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    # ==========================================
    # CLEANUP
    # ==========================================

    finally:

        if temp_pdf_path and os.path.exists(temp_pdf_path):

            try:
                os.remove(temp_pdf_path)

            except Exception:
                pass
