from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
)

from io import BytesIO

import pikepdf

unlock_pdf_bp = Blueprint("unlock_pdf", __name__)


@unlock_pdf_bp.route("/unlock_pdf", methods=["GET", "POST"])
def unlock_pdf():

    if request.method == "POST":

        pdf_file = request.files.get("pdfs")

        pdf_password = request.form.get("pdf_password", "")

        if not pdf_file:

            flash("Please upload PDF file", "error")

            return redirect(url_for("unlock_pdf.unlock_pdf"))

        try:

            input_stream = BytesIO(pdf_file.read())

            output_stream = BytesIO()

            with pikepdf.open(input_stream, password=pdf_password) as pdf:

                pdf.save(output_stream)

            output_stream.seek(0)

            return send_file(
                output_stream,
                as_attachment=True,
                download_name=f"unlocked_{pdf_file.filename}",
                mimetype="application/pdf",
            )

        except pikepdf.PasswordError:

            flash("Incorrect PDF password", "error")

            return redirect(url_for("unlock_pdf.unlock_pdf"))

        except Exception:

            flash("Unable to unlock PDF", "error")

            return redirect(url_for("unlock_pdf.unlock_pdf"))

    return render_template("unlock_pdf.html")
