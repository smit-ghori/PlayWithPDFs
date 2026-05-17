from flask import Blueprint, render_template

protect_pdf_bp = Blueprint("protect_pdf", __name__)

@protect_pdf_bp.route("/protect_pdf")
def protect_pdf():
    return render_template("protect_pdf.html")