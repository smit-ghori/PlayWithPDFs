#!/usr/bin/env bash

apt-get update && apt-get install -y libreoffice libreoffice-writer ghostscript fonts-dejavu-core

pip install -r requirements.txt

echo "🔥 Installing Playwright Chromium..."
python -m playwright install chromium