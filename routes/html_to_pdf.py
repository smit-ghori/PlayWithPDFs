from flask import Blueprint, render_template, request

html_to_pdf_bp = Blueprint("html_to_pdf", __name__)

@html_to_pdf_bp.route("/html_to_pdf", methods=["GET", "POST"])
def html_to_pdf():
    if request.method == "POST":
        url = request.form.get("url")   # get input value
        print("Entered URL:", url)      # print in terminal
        
    return render_template("html_to_pdf.html")