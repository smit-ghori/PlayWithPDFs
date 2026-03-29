import io
import fitz
from flask import Blueprint, render_template, request, send_file
from deep_translator import GoogleTranslator

translate_bp = Blueprint("translate", __name__)

LANGUAGES = {
    code: name.capitalize()
    for name, code in GoogleTranslator().get_supported_languages(as_dict=True).items()
}

@translate_bp.route("/translate", methods=["GET", "POST"])
@translate_bp.route("/translate/", methods=["GET", "POST"])
def translate():
    if request.method == "POST":
        files = request.files.getlist("pdfs")
        lang = request.form.get("lang", "hi")

        if not files:
            return "No PDF uploaded", 400

        doc = fitz.open(stream=files[0].read(), filetype="pdf")
        translator = GoogleTranslator(source="auto", target=lang)

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            inserts = []

            for blk in blocks:
                if blk.get("type", 0) != 0:
                    continue

                lines = blk.get("lines", [])
                if not lines:
                    continue

                rect = fitz.Rect(blk["bbox"])
                text = " ".join(
                    span["text"]
                    for line in lines
                    for span in line.get("spans", [])
                    if span.get("text", "").strip()
                ).strip()

                if not text:
                    continue

                span0 = lines[0]["spans"][0]
                fontsize = span0.get("size", 10)
                color = span0.get("color", 0)

                try:
                    translated = translator.translate(text)
                except Exception:
                    translated = text

                inserts.append((rect, translated, fontsize, color))

            for rect, _, _, _ in inserts:
                page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

            for rect, translated, fontsize, color in inserts:
                page.insert_textbox(
                    rect,
                    translated,
                    fontsize=fontsize,
                    color=(0, 0, 0),
                    fontname="helv",
                    align=0
                )

        output = io.BytesIO()
        doc.save(output, garbage=4, deflate=True)
        doc.close()
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="translated.pdf",
            mimetype="application/pdf"
        )

    return render_template("translate.html", languages=LANGUAGES)
