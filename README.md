# 📄 PlayWithPDFs

<div align="center">

🚀 **All-in-One PDF Toolkit for Modern Web**
Organize, convert, edit, and secure PDFs effortlessly — right in your browser.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20Site-blue?style=for-the-badge&logo=google-chrome)](https://playwithpdfs.onrender.com)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

### 🖼️ Preview

<!-- Add a screenshot or short GIF of the homepage / a feature in action here.
     This is the first thing recruiters and visitors see — a picture sells the
     project faster than any bullet list. -->

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Highlight Feature — JPG to PDF](#-highlight-feature--jpg-to-pdf)
- [Tech Stack](#️-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Overview

**PlayWithPDFs** is a powerful web application designed to handle all your PDF needs in one place.
From converting images to PDFs to editing, optimizing, and securing documents — everything is just a few clicks away, with no files stored permanently on the server.

---

## 🚀 Features

### 📂 Organize PDF
- Merge multiple PDFs into one
- Split PDFs into separate files
- Remove or extract specific pages
- Reorder pages easily
- Scan documents into PDF

### ⚡ Optimize PDF
- Compress PDF size efficiently
- Repair corrupted PDF files
- Perform OCR on scanned PDFs

### 🔄 Convert to PDF
- JPG → PDF
- Word → PDF
- PowerPoint → PDF
- Excel → PDF
- HTML → PDF

### 🔁 Convert from PDF
- PDF → JPG
- PDF → Word
- PDF → PowerPoint
- PDF → Excel
- PDF → PDF/A

### ✏️ Edit PDF
- Rotate PDF pages
- Add page numbers
- Insert watermark
- Crop pages
- Basic PDF editing tools

### 🔐 PDF Security
- Unlock protected PDFs
- Add password protection
- Digitally sign PDFs
- Redact sensitive content
- Compare two PDFs

### 🧠 PDF Intelligence
- Translate PDF content into different languages

---

## 🌟 Highlight Feature — JPG to PDF

A fully interactive and optimized image-to-PDF converter:

- 🖱️ Drag & drop image upload
- 🔄 Reorder images before conversion
- 📱 Mobile-friendly drag behavior
- 📄 Convert into:
  - Single merged PDF
  - Multiple PDFs (ZIP download)
- 📏 Margin control (None / Small / Large)
- 📐 Automatic A4 page fitting
- ⚡ Instant download (no server storage)

---

## 🛠️ Tech Stack

| Layer             | Technology         |
|-------------------|---------------------|
| Backend           | Flask (Python)      |
| Frontend          | HTML, CSS, JavaScript |
| Image Processing  | Pillow               |
| PDF Handling      | pypdf                |
| Rendering         | PyMuPDF               |
| Translation       | deep-translator       |

---

## 🏁 Getting Started

Run it locally in a few steps:

```bash
# Clone the repo
git clone https://github.com/smit-ghori/PlayWithPDFs.git
cd PlayWithPDFs

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Then open **http://localhost:5000** in your browser.

> Or skip setup entirely and try the [live demo](https://playwithpdfs.onrender.com).

---

## 📁 Project Structure

```
PlayWithPDFs/
├── app.py                 # Flask entry point
├── static/                 # CSS, JS, images
├── templates/               # HTML templates
├── requirements.txt
└── README.md
```

<!-- Update this to match your actual folder layout -->

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📬 Contact

**Smit Ghori**
- GitHub: [@smit-ghori](https://github.com/smit-ghori)

<div align="center">

If you found this project useful, consider giving it a ⭐!

</div>
