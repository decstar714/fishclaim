# FishClaim Backend

FastAPI backend for FishClaim. Provides auth, waters/zones, catches, and claim routes backed by PostgreSQL/PostGIS. Dockerized for local dev and deployed via docker-compose.

## Tech stack
- FastAPI + Uvicorn
- SQLAlchemy
- PostgreSQL/PostGIS
- Docker + docker-compose

## Getting started (local Python)
1. `python -m venv .venv`
2. `source .venv/bin/activate` (Windows: `./.venv/Scripts/activate`)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set values (e.g. `DATABASE_URL=postgresql+psycopg2://user:password@fishclaim_db:5432/fishclaim`, `SECRET_KEY=...`).
5. Run the API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Running with Docker
From the backend repo root (`/home/conor/fishclaim/backend`):
1. `cp .env.example .env` and update values (use `fishclaim_db` as the host if you are attaching to the existing Postgres/PostGIS container). `SECRET_KEY` must be set to a non-default value for any deployed environment.
2. Ensure the Docker network `fishclaim_default` exists (created by the current stack). If missing, create it: `docker network create fishclaim_default`.
3. Build and start the backend: `docker compose up -d --build backend`
4. API will be on port `8080` by default (override with `BACKEND_PORT` in `.env`).

Docker build uses `Dockerfile` with `requirements.txt` and the `app/` directory.

## Connecting to the FishClaim frontend
To run the full stack locally with the `fishclaim` frontend repository:

1. Clone both repos side by side, e.g.:
   ```bash
   git clone <frontend_repo_url> ../fishclaim
   ```
2. Copy `.env.example` to `.env` in this backend repo and set values (ensure `CORS_ORIGINS` includes the frontend dev host, e.g. `http://localhost:5173`).
3. Start the backend (Docker or local Python). With Docker:
   ```bash
   docker network create fishclaim_default  # only if the network does not already exist
   docker compose up -d --build backend
   ```
   The API will be reachable at `http://localhost:8080/api` by default.
4. In the frontend repo, configure its API base URL to point to the backend (for Vite apps this is typically an env var like `VITE_API_BASE=http://localhost:8080/api`).
5. Run the frontend dev server (commonly `npm install && npm run dev -- --host --port 5173`).

With this setup the default CORS values allow the frontend dev server to call the backend without additional changes.

### Configuration
- `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES` are read from environment variables (or `.env`).
- `CORS_ORIGINS` can be provided as a comma-separated list to control allowed front-end origins (defaults to localhost dev ports).
- `CLAIM_LIFETIME_DAYS` controls how long a claim stays active without being refreshed by the owner.
- Placeholder map endpoints return empty data at `/api/rivers` and `/api/claims` to keep the map client happy until real geometry is wired.

## Deploy script (server)
- `./deploy.sh [branch]` (default branch is `main`) will `git pull`, build the backend image, and restart the backend container without touching the database container.

## Branching model
- `main`: stable / production
- `dev`: integration
- `feature/*`: feature branches

## Notes
- Secrets should never be committed. Keep real values in `.env` (gitignored) using `.env.example` as a template.
- If you add new config keys, update `.env.example` and this README.

## Seeding the database
The seed script creates a default owner account, starter water/zone data, and species. Configure credentials in `.env` with:
```
SEED_USER_EMAIL=owner@example.com
SEED_USER_USERNAME=owner
SEED_USER_DISPLAY_NAME=FishClaim Owner
SEED_USER_PASSWORD=ChangeMe!123   # change this before using anywhere real
SEED_FORCE_RESET=true             # reset the password if the user already exists
```

Run inside the backend container (Docker) or your virtualenv:
```
python -m app.seed
# or: docker exec -it fishclaim_backend python -m app.seed
```

When `SEED_FORCE_RESET=true`, re-running the seed will rotate the password for the seeded user instead of skipping if it already exists.

## Session logging + claim refresh
- New table: `sessions` for recording time on water (zone, optional species, optional best_length_cm).
- Endpoint: `POST /api/sessions` (auth required) to log a session. Providing `species_id` lets the owner refresh an existing claim's timer; include `best_length_cm` to update length if it's better.
- Claim decay: claims automatically expire after `CLAIM_LIFETIME_DAYS` unless refreshed by the owner (via a catch or a session).
