FROM python:3.12

WORKDIR /app

COPY . .

# System dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    ghostscript \
    fonts-dejavu-core \
    wget \
    ca-certificates

# Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONUNBUFFERED=1
RUN python -m playwright install --with-deps chromium

# Start app
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 180 main:app
