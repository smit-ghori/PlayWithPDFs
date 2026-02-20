import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# 🔹 Common File Save Function
def save_uploaded_files(files):
    unique_id = str(uuid.uuid4())
    user_folder = os.path.join(UPLOAD_FOLDER, unique_id)
    os.makedirs(user_folder, exist_ok=True)

    saved_files = []

    for file in files:
        if file and file.filename != "":
            file_path = os.path.join(user_folder, file.filename)
            file.save(file_path)
            saved_files.append(file.filename)

    return unique_id, saved_files

# 🔹 Home Route
@app.route('/')
def home():
    return render_template("home.html")


# 🔹 Merge Route (GET + POST)
@app.route('/merge', methods=['GET', 'POST'])
def merge():
    if request.method == "POST":
        files = request.files.getlist('pdfs')
        folder_id, saved_files = save_uploaded_files(files)

        # 👉 Add merge logic here

        return redirect(url_for("download", folder_id=folder_id))

    return render_template("merge.html")


# 🔹 Compress Route (GET + POST)
@app.route('/compress', methods=['GET', 'POST'])
def compress():
    if request.method == "POST":
        files = request.files.getlist('pdfs')
        folder_id, saved_files = save_uploaded_files(files)

        # 👉 Add compress logic here

        return redirect(url_for("download", folder_id=folder_id))

    return render_template("compress.html")


# 🔹 Download Page
@app.route('/download/<folder_id>')
def download(folder_id):
    folder_path = os.path.join(UPLOAD_FOLDER, folder_id)

    if not os.path.exists(folder_path):
        return "Folder not found", 404

    files = os.listdir(folder_path)
    return render_template("download.html", files=files, folder_id=folder_id)


# 🔹 Download File Route
@app.route('/download-file/<folder_id>/<filename>')
def download_file(folder_id, filename):
    folder_path = os.path.join(UPLOAD_FOLDER, folder_id)
    return send_from_directory(folder_path, filename, as_attachment=True)


# 🔹 Run App
if __name__ == '__main__':
    app.run(debug=True)