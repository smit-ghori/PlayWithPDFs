FROM python:3.12-slim

WORKDIR /app

# System dependencies
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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Chromium path
ENV CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium

# Skip Playwright browser download
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Better logs
ENV PYTHONUNBUFFERED=1

# Flask production safety
ENV PYTHONDONTWRITEBYTECODE=1

# Copy project files
COPY . .

# Expose port
EXPOSE 10000

# Start Gunicorn
CMD gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 180 \
    main:app