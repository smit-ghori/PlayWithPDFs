import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from pypdf import PdfWriter

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# 🔹 Save Uploaded Files
def save_uploaded_files(files):
    unique_id = str(uuid.uuid4())
    user_folder = os.path.join(UPLOAD_FOLDER, unique_id)
    os.makedirs(user_folder, exist_ok=True)

    saved_files = []

    for file in files:
        if file and file.filename != "":
            file_path = os.path.join(user_folder, file.filename)
            file.save(file_path)
            saved_files.append(file_path)

    return unique_id, saved_files


# 🔹 Home Page
@app.route('/')
def home():
    return render_template("home.html")


# 🔹 Merge PDFs
@app.route('/merge', methods=['GET', 'POST'])
def merge():
    if request.method == "POST":

        files = request.files.getlist('pdfs')
        folder_id, saved_files = save_uploaded_files(files)

        writer = PdfWriter()

        # Merge PDFs
        for pdf in saved_files:
            writer.append(pdf)

        result_folder = os.path.join(UPLOAD_FOLDER, folder_id, "result")
        os.makedirs(result_folder, exist_ok=True)

        output_path = os.path.join(result_folder, "merged.pdf")

        writer.write(output_path)
        writer.close()

        return redirect(url_for("download", folder_id=folder_id))

    return render_template("merge.html")


# 🔹 Compress Page (logic can be added later)
@app.route('/compress', methods=['GET', 'POST'])
def compress():
    if request.method == "POST":

        files = request.files.getlist('pdfs')
        folder_id, saved_files = save_uploaded_files(files)

        # Compression logic can go here

        return redirect(url_for("download", folder_id=folder_id))

    return render_template("compress.html")


# 🔹 Download Page
@app.route('/download/<folder_id>')
def download(folder_id):

    folder_path = os.path.join(UPLOAD_FOLDER, folder_id)
    result_path = os.path.join(folder_path, "result")

    files = []

    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            if os.path.isfile(os.path.join(folder_path, file)):
                files.append(file)

    if os.path.exists(result_path):
        for file in os.listdir(result_path):
            files.append(f"result/{file}")

    return render_template("download.html", files=files, folder_id=folder_id)


# 🔹 Download File
@app.route('/download-file/<folder_id>/<path:filename>')
def download_file(folder_id, filename):

    folder_path = os.path.join(UPLOAD_FOLDER, folder_id)
    return send_from_directory(folder_path, filename, as_attachment=True)


# 🔹 Run Flask App
if __name__ == '__main__':
    app.run(debug=True)