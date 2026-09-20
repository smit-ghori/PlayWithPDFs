from dotenv import load_dotenv
load_dotenv()

import os
import threading
from flask import Flask
from extensions import mail, db
from routes.admin import admin_bp
from utils.tracking import init_tracking, seed_tools
from routes.home import home_bp
from routes.merge import merge_bp
from routes.download import download_bp
from routes.compress import compress_bp
from routes.split import split_bp
from routes.extract_pages import extract_pages_bp
from routes.remove_pages import remove_pages_bp
from routes.repair import repair_bp
from routes.translate import translate_bp
from routes.jpg_to_pdf import jpg_to_pdf_bp
from routes.word_to_pdf import word_to_pdf_bp
from routes.pdf_to_jpg import pdf_to_jpg_bp
from routes.html_to_pdf import html_to_pdf_bp
from routes.excel_to_pdf import excel_to_pdf_bp
from routes.ppt_to_pdf import ppt_to_pdf_bp
from routes.pdf_to_ppt import pdf_to_ppt_bp
from routes.pdf_to_word import pdf_to_word_bp
from routes.ocr_to_pdf import ocr_to_pdf_bp
from routes.pdf_to_excel import pdf_to_excel_bp
from routes.rotate_pdf import rotate_pdf_bp
from routes.add_page_number import add_page_number_bp
from routes.add_watermark import add_watermark_bp
from routes.crop_pdf import crop_pdf_bp
from routes.edit_pdf import edit_pdf_bp
from routes.unlock_pdf import unlock_pdf_bp
from routes.protect_pdf import protect_pdf_bp
from routes.sign_pdf import sign_pdf_bp
from routes.redact_pdf import redact_pdf_bp
from routes.compare_pdf import compare_pdf_bp
from routes.pdf_to_pdfA import pdf_to_pdfA_bp
from routes.organize_pdf import organize_pdf_bp
from routes.about import about_bp
from routes.contact_us import contact_us_bp
from utils.file_utils import cleanup_worker

app = Flask(__name__)

# MAIL CONFIG
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
mail.init_app(app)


app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-secret")

# DATABASE & ADMIN CONFIG
raw_url = os.environ.get("DATABASE_URL")
if not raw_url:
    raw_url = "sqlite:///playwithpdfs.db"
elif raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
if not raw_url.startswith("sqlite"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,     # hosted Postgres drops idle connections
        "pool_recycle": 280,
        "pool_size": 5,
        "max_overflow": 5,
    }
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024   # hard 200 MB upload ceiling
db.init_app(app)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# register routes
app.register_blueprint(admin_bp)
app.register_blueprint(home_bp)
app.register_blueprint(merge_bp)
app.register_blueprint(download_bp)
app.register_blueprint(compress_bp)
app.register_blueprint(split_bp)
app.register_blueprint(remove_pages_bp)
app.register_blueprint(extract_pages_bp)
app.register_blueprint(repair_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(jpg_to_pdf_bp)
app.register_blueprint(word_to_pdf_bp)
app.register_blueprint(pdf_to_jpg_bp)
app.register_blueprint(html_to_pdf_bp)
app.register_blueprint(excel_to_pdf_bp)
app.register_blueprint(ppt_to_pdf_bp)
app.register_blueprint(pdf_to_ppt_bp)
app.register_blueprint(pdf_to_word_bp)
app.register_blueprint(ocr_to_pdf_bp)
app.register_blueprint(pdf_to_excel_bp)
app.register_blueprint(rotate_pdf_bp)
app.register_blueprint(add_watermark_bp)
app.register_blueprint(add_page_number_bp)
app.register_blueprint(crop_pdf_bp)
app.register_blueprint(edit_pdf_bp)
app.register_blueprint(unlock_pdf_bp)
app.register_blueprint(protect_pdf_bp)
app.register_blueprint(sign_pdf_bp)
app.register_blueprint(redact_pdf_bp)
app.register_blueprint(compare_pdf_bp)
app.register_blueprint(pdf_to_pdfA_bp)
app.register_blueprint(about_bp)
app.register_blueprint(organize_pdf_bp)
app.register_blueprint(contact_us_bp)

# TRACKING & TOOL MANAGEMENT
init_tracking(app)

with app.app_context():
    import models  # noqa: F401  (registers tables)
    db.create_all()
    seed_tools(app)


# CLI COMMAND TO CREATE ADMIN
@app.cli.command("create-admin")
def create_admin():
    """flask create-admin"""
    import getpass
    from models import AdminUser
    email = input("Email: ").lower().strip()
    name = input("Name: ")
    password = getpass.getpass("Password: ")
    user = AdminUser(email=email, name=name, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print("Created admin user:", email)


# start cleanup thread
threading.Thread(target=cleanup_worker, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

# edited for compress
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
