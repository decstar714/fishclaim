#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BRANCH="${1:-main}"

cd "$PROJECT_DIR"

echo "Deploying FishClaim backend from branch: $BRANCH"

if command -v git >/dev/null 2>&1; then
  echo "Updating repository..."
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  echo "Git not available; skipping pull."
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose not found. Please install Docker Compose v2."
  exit 1
fi

echo "Building backend image..."
docker compose build backend

echo "Starting backend container..."
docker compose up -d backend

echo "Deployment complete. Verify logs with: docker compose logs -f backend"
