#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python - <<'PY'
import os
from pathlib import Path

path = Path(os.environ.get("CHROMIUM_EXECUTABLE_PATH", "/usr/bin/chromium"))

if not path.is_file():
    raise SystemExit(f"System Chromium was not found at {path}")

print(f"System Chromium found: {path}")
PY
