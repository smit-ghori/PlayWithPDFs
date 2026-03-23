import os
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files
from googletrans import LANGUAGES, Translator
from pdf2docx import Converter
from docx import Document
import pypandoc

translate_bp = Blueprint("translate", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


def translate_pdf(input_pdf, output_pdf, target_lang="hi"):
    docx_file = "temp.docx"
    translated_docx = "translated.docx"

    # Step 1: PDF → DOCX
    cv = Converter(input_pdf)
    cv.convert(docx_file)
    cv.close()

    doc = Document(docx_file)
    translator = Translator()

    # 🔥 FAST translation (paragraph-wise)
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            try:
                para.text = translator.translate(text, dest=target_lang).text
            except Exception as e:
                print("Para translate failed:", e)

    # 🔥 Tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text.strip()
                if text:
                    try:
                        cell.text = translator.translate(text, dest=target_lang).text
                    except Exception as e:
                        print("Cell translate failed:", e)

    # Save DOCX
    doc.save(translated_docx)

    # ✅ Step 3: DOCX → PDF (DEPLOYMENT SAFE)
    try:
        pypandoc.convert_file(translated_docx, 'pdf', outputfile=output_pdf)
    except Exception as e:
        print("Pandoc failed:", e)
        raise RuntimeError("PDF conversion failed")

    # Cleanup
    if os.path.exists(docx_file):
        os.remove(docx_file)
    if os.path.exists(translated_docx):
        os.remove(translated_docx)


@translate_bp.route("/translate", methods=["GET", "POST"])
def translate():

    if request.method == "POST":
        files = request.files.getlist("pdfs")

        if not files:
            return "No files uploaded", 400

        folder_id, saved_files = save_uploaded_files(files)

        # default language
        lang = request.form.get("lang", "hi")

        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        successful_files = []

        for pdf in saved_files:
            filename = os.path.basename(pdf)
            name_without_ext = os.path.splitext(filename)[0]

            output_file_path = os.path.join(
                result_folder,
                f"{name_without_ext}_translated_{lang}.pdf"
            )

            try:
                translate_pdf(pdf, output_file_path, lang)

                if os.path.exists(output_file_path):
                    successful_files.append(output_file_path)

            except Exception as e:
                print("Translate failed:", filename, e)

        if not successful_files:
            return "Translation failed", 500

        return redirect(url_for("download.download_file", folder_id=folder_id))

    return render_template("translate.html", languages=LANGUAGES)