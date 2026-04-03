import os
import threading
from flask import Flask
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
from utils.file_utils import cleanup_worker

app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads"   )
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# register routes
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

# start cleanup thread
threading.Thread(target=cleanup_worker, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    
# edited for compress
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)