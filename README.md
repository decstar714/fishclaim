# FishClaim Backend

FastAPI backend for FishClaim — a territory game where the biggest fish caught in a
stretch of river holds that stretch, until someone catches a bigger one or the claim
goes stale.

Provides auth, waters/zones, catches, sessions and claim routes, backed by PostgreSQL.
Dockerized for local dev and deployed via docker-compose.

## Tech stack
- FastAPI + Uvicorn
- SQLAlchemy 2.0
- PostgreSQL (`postgres:15-alpine`)
- Docker + docker-compose

> **Not PostGIS.** Earlier notes described this as PostGIS-backed; it is not. There are
> no geometry columns, no GeoAlchemy2 and no `ST_` calls anywhere. Positions are plain
> `lat`/`lng` floats on a catch, and zones are ordered records rather than polygons. If
> real geometry is ever needed — zone boundaries, point-in-polygon claim resolution —
> that is the point at which PostGIS becomes a genuine dependency.

## How a claim works

The whole game is one rule: **per zone, per species, the longest fish holds the claim.**

```mermaid
flowchart TD
    C["Catch logged<br/><i>zone + species + length_cm</i>"] --> Q["find the ACTIVE claim<br/>for this zone+species"]
    Q --> EXP{"older than<br/>CLAIM_LIFETIME_DAYS?"}
    EXP -->|yes| DEAD["mark inactive<br/><i>claim decayed</i>"] --> NEW
    EXP -->|no| MINE{"is it already mine?"}
    MINE -->|yes| REFRESH["reset the timer<br/>raise length if this fish is bigger"]
    MINE -->|no| BIG{"is my fish longer?"}
    BIG -->|no| KEEP["their claim stands"]
    BIG -->|yes| TAKE["their claim -> inactive"] --> NEW["insert my claim<br/><i>is_active = true</i>"]

    style KEEP fill:#7a2020,stroke:#4a1010,color:#fff
    style NEW fill:#2d5a3d,stroke:#1a3a26,color:#fff
    style DEAD fill:#8a5a1a,color:#fff
```

Two things follow from this that are not obvious:

**Claims decay.** A claim expires after `CLAIM_LIFETIME_DAYS` unless the owner refreshes
it — by catching again, or by logging a session on the water (`POST /api/sessions`). You
have to keep showing up to hold water, which is the point.

**Beaten claims are kept, not deleted.** They stay as rows with `is_active=false`, so a
zone has a history rather than just a current holder. That history is why the uniqueness
rule is a **partial** unique index on `(zone_id, species_id) WHERE is_active` — a plain
unique constraint that included `is_active` would also limit you to one *inactive* row
per zone, and the third time a claim changed hands the insert would fail. See the comment
in `app/models.py`.

## Data model

```mermaid
erDiagram
    USER  ||--o{ CATCH   : logs
    USER  ||--o{ CLAIM   : holds
    WATER ||--o{ ZONE    : "divided into"
    ZONE  ||--o{ CATCH   : "caught in"
    ZONE  ||--o{ CLAIM   : "claimed by"
    SPECIES ||--o{ CATCH : "of"
    CATCH ||--o| CLAIM   : "backs"

    CATCH { float length_cm float lat float lng datetime caught_at }
    CLAIM { float length_cm bool is_active datetime created_at datetime revoked_at }
    ZONE  { int order_index string name }
```

A claim always points at the `catch` that earned it, so "who holds this pool and with
what fish" is answerable without recomputing anything.

## Getting started (local Python)
1. `python -m venv .venv`
2. `source .venv/bin/activate` (Windows: `./.venv/Scripts/activate`)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set values (e.g. `DATABASE_URL=postgresql+psycopg2://user:password@fishclaim_db:5432/fishclaim`, `SECRET_KEY=...`).
5. Run the API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Running with Docker
From the backend repo root:
1. `cp .env.example .env` and update values (use `fishclaim_db` as the host if you are attaching to the existing Postgres container). `SECRET_KEY` must be set to a non-default value for any deployed environment.
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

### ⚠️ The JWT signing key in this repo's history is public

Early commits hardcoded `SECRET_KEY` in `app/auth.py` with a `# change later`
comment. This repository is public, so that value must be treated as compromised
forever — rewriting history would not help, since the old objects may already be
cloned, cached or indexed.

Current code reads the key from settings (`app/config.py`), and the local `.env`
has been rotated to a fresh 64-character value. If you deploy this anywhere:

- generate your own key, never reuse one from history:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
- any environment still signing with the old key can have tokens forged against
  it by anyone who reads the git log. Rotate it before exposing an instance.

Rotating the key invalidates every issued token, so all users must log in again.

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
