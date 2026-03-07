import os, zipfile
import uuid
import shutil
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, send_file
from pypdf import PdfWriter
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 🔹 Save uploaded PDFs
def save_uploaded_files(files):

    unique_id = str(uuid.uuid4())
    user_folder = os.path.join(UPLOAD_FOLDER, unique_id)

    os.makedirs(user_folder, exist_ok=True)

    saved_files = []

    for file in files:
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file_path = os.path.join(user_folder, filename)

            file.save(file_path)
            saved_files.append(file_path)

    return unique_id, saved_files


# Zipping file 
def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


# 🔹 Home page
@app.route("/")
def home():
    return render_template("index.html")


# 🔹 Compress PDFs (placeholder)
@app.route("/compress", methods=["GET", "POST"])
def compress():
    # this view exists primarily so url_for('compress') works in templates
    if request.method == "POST":
        pass
    return render_template("compress.html")


# 🔹 Merge PDFs
@app.route("/merge", methods=["GET", "POST"])
def merge():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        folder_id, saved_files = save_uploaded_files(files)

        writer = PdfWriter()

        for pdf in saved_files:
            writer.append(pdf)

        # result folder
        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        output_path = os.path.join(result_folder, "merged.pdf")

        writer.write(output_path)
        writer.close()

        return redirect(url_for("download_file", folder_id=folder_id))

    return render_template("merge.html")


# 🔹 Download result file
@app.route("/download/<folder_id>")
def download_file(folder_id):

    result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")

    if not os.path.exists(result_folder):
        return "Result not found", 404

    files = os.listdir(result_folder)

    if not files:
        return "No output generated", 400

    # Single file
    if len(files) == 1:
        file_path = os.path.join(result_folder, files[0])
        return send_file(file_path, as_attachment=True)

    # Multiple files → zip
    zip_path = os.path.join(UPLOAD_FOLDER, folder_id, "download.zip")

    if not os.path.exists(zip_path):
        zip_folder(result_folder, zip_path)

    return send_file(zip_path, as_attachment=True)

# 🔹 Background deleting system
def cleanup_worker():

    while True:

        now = time.time()

        for folder in os.listdir(UPLOAD_FOLDER):

            folder_path = os.path.join(UPLOAD_FOLDER, folder)

            if os.path.isdir(folder_path):

                folder_age = now - os.path.getmtime(folder_path)

                # delete folders older than 10 minutes
                if folder_age > 600:
                    shutil.rmtree(folder_path, ignore_errors=True)
                    print("Deleted old folder:", folder_path)

        time.sleep(300)  # run every 5 minutes


# 🔹 Start cleanup thread
threading.Thread(target=cleanup_worker, daemon=True).start()


# 🔹 Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)