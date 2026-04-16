#!/usr/bin/env bash
set -e

echo "📦 Installing system dependencies..."
apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    ghostscript \
    fonts-dejavu-core \
    wget \
    ca-certificates

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Installing Playwright Chromium (FIXED PATH)..."

# ✅ VERY IMPORTANT: consistent path
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright

# Install browser
python -m playwright install --with-deps chromium

echo "✅ Build completed successfully"
