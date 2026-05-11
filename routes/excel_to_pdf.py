from flask import Blueprint, render_template

excel_to_pdf_bp = Blueprint("excel_to_pdf", __name__)

@excel_to_pdf_bp.route("/excel_to_pdf")
def excel_to_pdf():
    return render_template("excel_to_pdf.html")