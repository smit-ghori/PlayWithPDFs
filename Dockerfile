FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ✅ SAME PATH (important)
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    ghostscript \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# LibreOffice path
ENV PATH="/usr/lib/libreoffice/program:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Install browser in SAME PATH
RUN python -m playwright install --with-deps chromium

COPY . .

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} main:app"]
