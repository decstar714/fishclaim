#!/usr/bin/env bash
#
# Pull a branch and restart the stack. The database container is deliberately
# left alone -- rebuilding it would drop the volume and take every claim with
# it, so this only ever touches backend and frontend.
#
#   ./deploy.sh            # deploys main
#   ./deploy.sh dev        # deploys dev
#
set -euo pipefail

DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$DEPLOY_DIR/.." && pwd)"
BRANCH="${1:-main}"

cd "$REPO_DIR"

echo "Deploying FishClaim from branch: $BRANCH"

if command -v git >/dev/null 2>&1; then
  echo "Updating repository..."
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  echo "Git not available; skipping pull."
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose not found. Install Docker Compose v2." >&2
  exit 1
fi

cd "$DEPLOY_DIR"

if [[ ! -f .env ]]; then
  echo "deploy/.env is missing. Copy .env.example and fill it in." >&2
  exit 1
fi

# Bring the database up first and wait for its healthcheck, so the API does not
# spend its first seconds failing to connect.
echo "Starting database..."
docker compose up -d db

echo "Building backend and frontend..."
docker compose build backend frontend

echo "Restarting application containers..."
docker compose up -d backend frontend

echo
echo "Done. Follow logs with:"
echo "  docker compose -f $DEPLOY_DIR/docker-compose.yml logs -f backend frontend"
