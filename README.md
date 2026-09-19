# PlayWithPDFs

PlayWithPDFs is a Flask-based web application that helps users work with PDF, image, and office files. It provides a simple interface to upload files and perform common document-processing tasks.

## Overview

This project is designed for:
- PDF editing and manipulation
- File format conversion
- OCR and translation
- Image and office document processing

## Features and Tools Used

### PDF Operations
- Merge PDFs using pypdf
- Split PDFs using pypdf
- Extract pages using pypdf
- Remove pages using pypdf
- Rotate pages using PyPDF2
- Add page numbers using PyPDF2
- Add watermarks using PyMuPDF (fitz)
- Crop PDFs using PyMuPDF
- Redact content using PyMuPDF
- Sign PDFs using PyMuPDF
- Compare PDFs using PyMuPDF
- Protect and unlock PDFs using PyPDF2
- Compress and repair PDFs using PDF processing libraries such as pikepdf

### Image and Document Conversion
- Convert images to PDF using Pillow
- Convert PDF to images using PyMuPDF
- Convert PDF to Word using pdf2docx
- Convert Word to PDF using python-docx
- Convert PDF to PowerPoint using python-pptx and PyMuPDF
- Convert PowerPoint to PDF using python-pptx
- Convert Excel to PDF and PDF to Excel using openpyxl, pandas, and pdfplumber
- Convert HTML to PDF using Playwright

### OCR and Translation
- Perform OCR on scanned PDFs using ocrmypdf, pytesseract, and PaddleOCR
- Translate PDF content using deep-translator

### Additional Features
- Convert PDF to PDF/A using PDF processing libraries
- Send contact form emails using Flask-Mail

## Tech Stack
- Python
- Flask
- PyPDF2 / pypdf
- PyMuPDF (fitz)
- Pillow
- pdf2docx
- python-docx
- python-pptx
- openpyxl
- pandas
- pdfplumber
- Playwright
- ocrmypdf
- pytesseract
- deep-translator
- Flask-Mail

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

3. Open the app in your browser at:
   ```text
   http://localhost:5000
   ```

## Conclusion

PlayWithPDFs is a document-processing platform built with Flask that combines PDF libraries, image tools, OCR engines, and office conversion libraries to provide a wide range of file-handling features.
