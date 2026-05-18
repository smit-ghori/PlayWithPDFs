from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
)
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus.tables import Table, TableStyle
import fitz
from difflib import SequenceMatcher

compare_pdf_bp = Blueprint("compare_pdf", __name__)


# =====================================================
# COMPARE PAGE
# =====================================================


@compare_pdf_bp.route("/compare_pdf")
def compare_pdf():
    return render_template("compare_pdf.html")


# =====================================================
# DOWNLOAD COMPARE REPORT
# =====================================================


@compare_pdf_bp.route("/compare_pdf", methods=["POST"])
def compare_pdf_report():

    files = request.files.getlist("pdfs")

    if len(files) < 2:
        return "Please upload 2 PDF files"

    pdf1 = files[0]
    pdf2 = files[1]

    # -----------------------------------------
    # EXTRACT TEXT
    # -----------------------------------------

    text1 = extract_pdf_text(pdf1)
    text2 = extract_pdf_text(pdf2)

    # -----------------------------------------
    # COMPARE
    # -----------------------------------------

    changes = compare_texts(text1, text2)

    # -----------------------------------------
    # GENERATE REPORT PDF
    # -----------------------------------------

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    elements = []

    # TITLE
    title = Paragraph("PDF Comparison Report", styles["Title"])

    elements.append(title)
    elements.append(Spacer(1, 20))

    # FILE NAMES
    file_info = Paragraph(
        f"""
        <b>Original PDF:</b> {pdf1.filename}<br/>
        <b>Modified PDF:</b> {pdf2.filename}
        """,
        styles["BodyText"],
    )

    elements.append(file_info)
    elements.append(Spacer(1, 20))

    # TOTAL CHANGES
    total = Paragraph(f"<b>Total Changes:</b> {len(changes)}", styles["Heading2"])

    elements.append(total)
    elements.append(Spacer(1, 16))

    # -----------------------------------------
    # TABLE DATA
    # -----------------------------------------

    table_data = [["Type", "Old Text", "New Text"]]

    for change in changes:

        table_data.append([change["type"], change["old"], change["new"]])

    table = Table(table_data, colWidths=[80, 220, 220])

    table.setStyle(
        TableStyle(
            [
                # HEADER
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                # BODY
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(table)

    # BUILD PDF
    doc.build(elements)

    buffer.seek(0)

    # -----------------------------------------
    # DOWNLOAD FILE
    # -----------------------------------------

    return send_file(
        buffer,
        as_attachment=True,
        download_name="compare_report.pdf",
        mimetype="application/pdf",
    )


# =====================================================
# EXTRACT PDF TEXT
# =====================================================


def extract_pdf_text(file):

    text = ""

    pdf = fitz.open(stream=file.read(), filetype="pdf")

    for page in pdf:

        text += page.get_text()

    pdf.close()

    return text


# =====================================================
# COMPARE TEXTS
# =====================================================


def compare_texts(text1, text2):

    words1 = text1.split()
    words2 = text2.split()

    matcher = SequenceMatcher(None, words1, words2)

    changes = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "equal":
            continue

        old_text = " ".join(words1[i1:i2])
        new_text = " ".join(words2[j1:j2])

        changes.append(
            {
                "type": tag.capitalize(),
                "old": old_text if old_text else "-",
                "new": new_text if new_text else "-",
            }
        )

    return changes
