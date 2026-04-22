#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m playwright install chromium

python - <<'PY'
import os
from pathlib import Path

root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")).expanduser()
if not root:
    root = Path.home() / ".cache" / "ms-playwright"

matches = (
    list(root.glob("chromium*/**/chrome"))
    + list(root.glob("chromium*/**/headless_shell"))
    + list(root.glob("chromium*/**/chrome-headless-shell"))
)

if not matches:
    raise SystemExit(f"Chromium was not installed under {root}")

print(f"Chromium installed: {matches[0]}")
PY
