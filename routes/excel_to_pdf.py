from flask import Blueprint, render_template, request, send_file
import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    Spacer,
    TableStyle,
    Paragraph,
    PageBreak,
)

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from io import BytesIO

excel_to_pdf_bp = Blueprint("excel_to_pdf", __name__)


# SHOW PAGE
@excel_to_pdf_bp.route("/excel_to_pdf")
def excel_to_pdf():
    return render_template("excel_to_pdf.html")


# CONVERT EXCEL TO PDF
@excel_to_pdf_bp.route("/excel_to_pdf", methods=["POST"])
def convert_excel_to_pdf():

    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        return "No files uploaded"

    # PDF memory buffer
    pdf_buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    elements = []

    styles = getSampleStyleSheet()

    for uploaded_file in uploaded_files:

        try:

            # Read all sheets
            excel_data = pd.ExcelFile(uploaded_file)

            for sheet_name in excel_data.sheet_names:

                # Read sheet
                df = pd.read_excel(excel_data, sheet_name=sheet_name)

                # Skip empty sheets
                if df.empty:
                    continue

                # Add file name
                elements.append(
                    Paragraph(
                        f"<b>File:</b> {uploaded_file.filename}",
                        styles["Heading1"],
                    )
                )

                elements.append(Spacer(1, 10))

                # Add sheet name
                elements.append(
                    Paragraph(
                        f"<b>Sheet:</b> {sheet_name}",
                        styles["Heading2"],
                    )
                )

                elements.append(Spacer(1, 10))

                # Convert dataframe to list
                data = [df.columns.tolist()] + df.values.tolist()

                # Create table
                table = Table(data, repeatRows=1)

                # Table styling
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ]
                    )
                )

                elements.append(table)

                elements.append(Spacer(1, 20))

                # Page break after each sheet
                elements.append(PageBreak())

        except Exception as e:
            return f"Error processing file {uploaded_file.filename}: {str(e)}"

    # Build PDF
    doc.build(elements)

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="excel_to_pdf.pdf",
        mimetype="application/pdf",
    )
