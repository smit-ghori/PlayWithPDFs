FROM python:3.12

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    chromium \
    ghostscript \
    fonts-dejavu-core \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Use Debian's Chromium package instead of Playwright's downloaded browser cache.
ENV CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PYTHONUNBUFFERED=1
RUN test -x "$CHROMIUM_EXECUTABLE_PATH"

COPY . .

# Start app
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 180 main:app
