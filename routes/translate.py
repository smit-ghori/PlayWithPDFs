import os
from flask import Blueprint, render_template, request, redirect, url_for
from utils.file_utils import save_uploaded_files
from deep_translator import GoogleTranslator
from pdf2docx import Converter
from docx import Document
import pypandoc
from googletrans import LANGUAGES, Translator

translate_bp = Blueprint("translate", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

@translate_bp.route("/translate", methods=["GET", "POST"])
def translate():
    if request.method == "POST":
        print("Hitted successfully")
    return render_template("translate.html", languages=LANGUAGES)