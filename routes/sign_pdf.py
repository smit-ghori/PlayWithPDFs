from flask import Blueprint, render_template, request, current_app, send_file, abort
from werkzeug.utils import secure_filename
import io, json
import fitz  # pymupdf

sign_pdf_bp = Blueprint("sign_pdf", __name__)


@sign_pdf_bp.route("/sign_pdf", methods=["GET", "POST"])
def sign_pdf():
    if request.method == "POST":
        # Get uploaded PDFs (use first PDF for signing)
        pdf_files = request.files.getlist("pdfs")
        if not pdf_files:
            return render_template("sign_pdf.html", error="No PDF uploaded")

        pdf_file = pdf_files[0]
        pdf_bytes = pdf_file.read()

        # Signature image
        sig_file = request.files.get("signature_image")
        if not sig_file:
            return render_template("sign_pdf.html", error="No signature image uploaded")
        sig_bytes = sig_file.read()

        # Placements metadata
        placements_raw = request.form.get("sig_placements", "[]")
        try:
            placements = json.loads(placements_raw)
        except Exception:
            placements = []

        # Open PDF from bytes
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            return render_template("sign_pdf.html", error=f"Failed to open PDF: {e}")

        # For each placement, insert the signature image
        for p in placements:
            try:
                page_num = int(p.get("page", 1)) - 1
                if page_num < 0 or page_num >= len(doc):
                    continue
                page = doc[page_num]

                # PDF page size in points
                pw = page.rect.width
                ph = page.rect.height

                # Canvas pixel dims sent from client (added by frontend)
                canvas_w = float(p.get("canvas_width_px") or pw)
                canvas_h = float(p.get("canvas_height_px") or ph)

                left = float(p.get("left", 0))
                top = float(p.get("top", 0))
                width = float(p.get("width", 0))
                height = float(p.get("height", 0))
                angle = float(p.get("angle", 0) or 0)

                # Convert pixel coordinates -> PDF points
                sx = pw / canvas_w
                sy = ph / canvas_h

                x = left * sx
                # convert top-left origin (browser) to PDF coordinates (top-left assumed for pymupdf)
                y = top * sy
                w = width * sx
                h = height * sy

                rect = fitz.Rect(x, y, x + w, y + h)

                # Insert image from bytes
                page.insert_image(rect, stream=sig_bytes, rotate=int(angle))
            except Exception:
                # Skip invalid placement entries
                continue

        # Save to BytesIO and send back
        # Write PDF to bytes and return via BytesIO
        try:
            pdf_bytes_out = doc.write()
        except Exception:
            out = io.BytesIO()
            doc.save(out)
            out.seek(0)
            return send_file(
                out,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="signed.pdf",
            )

        out = io.BytesIO(pdf_bytes_out)
        out.seek(0)
        return send_file(
            out,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="signed_by_PlayWithPDFs.pdf",
        )

    return render_template("sign_pdf.html")
