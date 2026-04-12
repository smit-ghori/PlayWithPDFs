#!/usr/bin/env bash

set -e

export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

apt-get update && apt-get install -y libreoffice libreoffice-writer ghostscript fonts-dejavu-core

pip install -r requirements.txt

echo "Installing Playwright Chromium..."
python -m playwright install --with-deps chromium
