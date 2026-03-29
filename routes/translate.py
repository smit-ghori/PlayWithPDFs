import os
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files
from deep_translator import GoogleTranslator

translate_bp = Blueprint("translate", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

# ✅ get all supported languages dynamically
LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)

@translate_bp.route("/translate", methods=["GET", "POST"])
@translate_bp.route("/translate/", methods=["GET", "POST"])
def translate():
    if request.method == "POST":
        print("Hitted successfully")

    return render_template("translate.html", languages=LANGUAGES)