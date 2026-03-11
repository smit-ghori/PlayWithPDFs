import os
import zipfile
import uuid
import shutil
import time
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


def zip_folder(folder_path, zip_path):

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:

        for root, dirs, files in os.walk(folder_path):

            for file in files:

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)

                zipf.write(file_path, arcname)


def cleanup_worker():

    while True:

        now = time.time()

        for folder in os.listdir(UPLOAD_FOLDER):

            folder_path = os.path.join(UPLOAD_FOLDER, folder)

            if os.path.isdir(folder_path):

                folder_age = now - os.path.getmtime(folder_path)

                if folder_age > 600:
                    shutil.rmtree(folder_path, ignore_errors=True)
                    print("Deleted old folder:", folder_path)

        time.sleep(300)