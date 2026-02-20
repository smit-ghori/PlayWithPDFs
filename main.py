import os
import uuid
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

# Create uploads folder if it does not exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/download.html')
def download():
    return render_template("download.html")

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/merge.html')
def merge():
    return render_template("merge.html")


@app.route('/compress.html')
def compress():
    return render_template("compress.html")


# ✅ Only for saving uploaded files
@app.route('/merge', methods=['POST'])
def upload_files():
    files = request.files.getlist('pdfs')

    # 🔥 Create unique folder using UUID
    unique_id = str(uuid.uuid4())
    user_folder = os.path.join(UPLOAD_FOLDER, unique_id)
    os.makedirs(user_folder, exist_ok=True)

    for file in files:
        if file.filename != "":
            file.save(os.path.join(user_folder, file.filename))

    return redirect(url_for("download"))


if __name__ == '__main__':
    app.run(debug=True)