FROM python:3.12-slim

WORKDIR /app

# ==========================================
# SYSTEM DEPENDENCIES
# ==========================================

RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-calc \
    libreoffice-writer \
    libreoffice-impress \
    chromium \
    ghostscript \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-guj \
    fonts-dejavu-core \
    wget \
    ca-certificates \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# COPY REQUIREMENTS
# ==========================================

COPY requirements.txt .

# ==========================================
# UPGRADE PIP
# ==========================================

RUN pip install --upgrade pip

# ==========================================
# INSTALL PYTHON PACKAGES
# ==========================================

RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# PLAYWRIGHT SETTINGS
# ==========================================

ENV CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# ==========================================
# PYTHON SETTINGS
# ==========================================

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ==========================================
# COPY PROJECT
# ==========================================

COPY . .

# ==========================================
# EXPOSE PORT
# ==========================================

EXPOSE 10000

# ==========================================
# START APP
# ==========================================

CMD gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 180 \
    main:app