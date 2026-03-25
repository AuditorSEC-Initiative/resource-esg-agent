#!/usr/bin/env bash
set -euo pipefail

# ResourceESGAgent — one-command production deploy
# Usage: bash deploy.sh [--env production|staging]

ENV=${1:---env}
ENV_NAME=${2:-production}

echo "==> ResourceESGAgent deploy: $ENV_NAME"

# 1. Pull latest
git pull origin main

# 2. Install Python deps
pip install -r requirements.txt --quiet

# 3. Run DB migrations
python -m alembic upgrade head || echo "[warn] alembic not configured, skipping migrations"

# 4. Load test/seed data (optional)
if [ "$ENV_NAME" = "staging" ]; then
  python load_test_data.py
  echo "==> Seed data loaded"
fi

# 5. Start FastAPI via uvicorn
if command -v uvicorn &>/dev/null; then
  echo "==> Starting API on port 8000"
  uvicorn agents.resource_esg.api:app --host 0.0.0.0 --port 8000 --workers 2 &
else
  echo "[error] uvicorn not found. Run: pip install uvicorn"
  exit 1
fi

# 6. Docker Compose (full stack)
if command -v docker &>/dev/null; then
  echo "==> Starting full stack with Docker Compose"
  docker compose up -d --build
  echo "==> Stack running. Services:"
  docker compose ps
else
  echo "[warn] Docker not found. API-only mode."
fi

echo "==> Deploy complete. API: http://localhost:8000/docs"
