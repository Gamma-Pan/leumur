#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export BUILDX_CONFIG="${BUILDX_CONFIG:-$PWD/.artifacts/buildx}"
python3 - <<'PY'
from pathlib import Path
import secrets
p=Path('.env')
if not p.exists():
    p.write_text('POSTGRES_PASSWORD='+secrets.token_urlsafe(32)+'\n')
    p.chmod(0o600)
PY
docker compose up -d --build
docker compose exec -T backend python -m app.ingest
