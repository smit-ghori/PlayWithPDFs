FROM python:3.12

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    ghostscript \
    fonts-dejavu-core \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONUNBUFFERED=1
RUN python -m playwright install --with-deps chromium
RUN python -c "from pathlib import Path; import os; root = Path(os.environ['PLAYWRIGHT_BROWSERS_PATH']); matches = list(root.glob('chromium*/**/chrome')) + list(root.glob('chromium*/**/headless_shell')) + list(root.glob('chromium*/**/chrome-headless-shell')); assert matches, f'Chromium was not installed under {root}'"

COPY . .

# Start app
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 180 main:app
