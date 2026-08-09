# FishClaim Backend

FastAPI backend for FishClaim. Provides auth, waters/zones, catches, and claim routes backed by PostgreSQL/PostGIS. Dockerized for local dev and compose.

## Tech stack
- FastAPI + Uvicorn
- SQLAlchemy
- PostgreSQL/PostGIS
- Docker + docker-compose

## Structure
- `app/main.py`: app factory, router includes.
- `app/core`: config (pydantic-settings), DB session, security/token helpers.
- `app/api/routes`: health, auth, waters, catches, claims.
- `app/api/deps`: shared FastAPI dependencies (auth).
- `app/models`, `app/schemas`: SQLAlchemy + Pydantic models.
- `tests/`: pytest starter (health).
- `docs/`: backend notes and session log.
- `scripts/`: helper scripts (session log).

## Getting started (local Python)
```bash
cd path/to/fishclaim-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # set DATABASE_URL, SECRET_KEY, etc.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running with Docker
```bash
cd path/to/fishclaim-backend
cp .env.example .env  # set real values
docker network create fishclaim_default  # if missing
docker compose up -d --build backend
# API on ${BACKEND_PORT:-8080} mapped to container 8000
```

## Frontend pairing
- Set backend CORS to include frontend origin via `CORS_ORIGINS` in `.env`.
- Configure frontend env (e.g., `VITE_API_BASE_URL=http://localhost:8080/api`).

## Configuration
- Environment via `.env` and pydantic-settings (`app/core/config.py`):
  - `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`.
- Update `.env.example` when adding new settings.

## Tests
```bash
source .venv/bin/activate
pip install pytest
pytest
```

## Session log
- Append entries to `docs/FISHCLAIM_SESSION_LOG.md` via `bash scripts/append_session_log.sh "summary"`.

## Notes
- Secrets should never be committed. Keep real values in `.env`.
- If you add new config keys, update `.env.example`, README, and docs.
