id = "4vjlwm"
import os
import io
import re
import tempfile
import pdfplumber
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

pdf_to_excel_bp = Blueprint("pdf_to_excel", __name__)


@pdf_to_excel_bp.route("/pdf_to_excel")
def pdf_to_excel():

    return render_template("pdf_to_excel.html")


@pdf_to_excel_bp.route("/convert_pdf_to_excel", methods=["POST"])
def convert_pdf_to_excel():

    temp_pdf_path = None

    try:

        uploaded_file = request.files.get("pdfs")

        if not uploaded_file:

            flash("Please upload a PDF file.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        filename = uploaded_file.filename.lower()

        if not filename.endswith(".pdf"):

            flash("Only PDF files are allowed.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        sheet_mode = request.form.get("sheet_mode", "single")

        separate_page_sheets = sheet_mode == "separate"

        pdf_bytes = uploaded_file.read()

        if not pdf_bytes:

            flash("Uploaded PDF is empty.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        temp_file.write(pdf_bytes)

        temp_file.close()

        temp_pdf_path = temp_file.name

        extracted_pages = {}

        with pdfplumber.open(temp_pdf_path) as pdf:

            for page_number, page in enumerate(pdf.pages, start=1):

                try:

                    text = page.extract_text()

                    if not text:
                        continue

                    lines = text.split("\n")

                    rows = []

                    for line in lines:

                        line = line.strip()

                        if not line:
                            continue

                        columns = re.split(r"\s{2,}", line)

                        if len(columns) == 1:

                            columns = line.split()

                        rows.append(columns)

                    if not rows:
                        continue

                    max_cols = max(len(r) for r in rows)

                    normalized_rows = []

                    for row in rows:

                        row += [""] * (max_cols - len(row))

                        normalized_rows.append(row)

                    df = pd.DataFrame(normalized_rows)

                    if df.empty:
                        continue

                    extracted_pages[page_number] = df

                except Exception as page_error:

                    print(f"PAGE {page_number} ERROR: " f"{str(page_error)}")

                    continue

        if not extracted_pages:

            flash("Could not extract data " "from this PDF.", "error")

            return redirect(url_for("pdf_to_excel.pdf_to_excel"))

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:

            if separate_page_sheets:

                for page_number, df in extracted_pages.items():

                    df.to_excel(
                        writer,
                        sheet_name=(f"Page_{page_number}")[:31],
                        index=False,
                        header=False,
                    )

            else:

                final_df = pd.DataFrame()

                for page_number, df in extracted_pages.items():

                    page_header = pd.DataFrame([[f"PAGE " f"{page_number}"]])

                    final_df = pd.concat([final_df, page_header, df], ignore_index=True)

                    empty_row = pd.DataFrame([[""]])

                    final_df = pd.concat([final_df, empty_row], ignore_index=True)

                final_df.to_excel(
                    writer, sheet_name="All_Pages", index=False, header=False
                )

        excel_buffer.seek(0)

        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=("converted_data.xlsx"),
            mimetype=(
                "application/vnd."
                "openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            ),
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        flash(f"ERROR: {str(e)}", "error")

        return redirect(url_for("pdf_to_excel.pdf_to_excel"))

    finally:

        if temp_pdf_path and os.path.exists(temp_pdf_path):

            try:

                os.remove(temp_pdf_path)

            except Exception:

                pass
