# FishClaim Backend

## Overview
- Purpose: API for FishClaim (waters, zones, catches, territory claims).
- Stack: FastAPI + Uvicorn, SQLAlchemy, PostgreSQL/PostGIS, JWT auth, Docker/Compose.
- App entry: `app/main.py` (`create_app()`), routers under `app/api/routes`.

## Layout
- `app/core`: settings, database session, security/token helpers.
- `app/api/routes`: health, auth, waters, catches, claims.
- `app/api/deps`: shared FastAPI deps (auth).
- `app/models`: SQLAlchemy models.
- `app/schemas`: Pydantic models.
- `tests/`: pytest starter (health endpoint).
- `Dockerfile`, `docker-compose.yml`: container build/run.

## Environment / config
- Copy `.env.example` → `.env` and set values:
  - `DATABASE_URL`: Postgres/PostGIS connection string (e.g., `postgresql+psycopg2://fishclaim:fishclaim@fishclaim-db:5432/fishclaim`).
  - `SECRET_KEY`: JWT signing secret.
  - `ALGORITHM`: JWT algorithm (default HS256).
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: token lifetime.
  - `CORS_ORIGINS`: comma-separated allowed origins (frontend dev servers).
- Settings live in `app/core/config.py` (pydantic-settings).

## Local dev (host)
```bash
cd path/to/fishclaim-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, SECRET_KEY, etc.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker / Compose
```bash
cd path/to/fishclaim-backend
cp .env.example .env   # set real values
docker network create fishclaim_default  # if missing
docker compose up -d --build backend     # maps ${BACKEND_PORT:-8080} -> container 8000
```

## Database and migrations
- PostGIS service defined in `docker-compose.yml` (image: `postgis/postgis:16-3.4`, defaults user/pass/db = `fishclaim`).
- `DATABASE_URL` should point to the PostGIS container (e.g., `postgresql+psycopg2://fishclaim:fishclaim@fishclaim-db:5432/fishclaim`).
- Startup runs `CREATE EXTENSION IF NOT EXISTS postgis` when on PostgreSQL; tables auto-created via SQLAlchemy metadata.
- Health endpoint `/api/health` checks DB connectivity.
- No migrations yet. Future: add Alembic with PostGIS support (e.g., include GeoAlchemy types, generate spatial indexes via migrations).

## Claim lifecycle
- Model: `Claim` uses `status` (active/expired/rejected), `expires_at`, `note`, `user_id` (from header), reach linkage.
- Rules: one active claim per reach; POST `/api/claims/` creates a claim if none active; conflicts return 409.
- Expiration: lazy helper `expire_stale_claims(db)` marks past-due active claims as expired; called at start of claim endpoints (and in catch-based claims). Upgrade path: background job/cron/Alembic migrations for indexes.

## Spatial design and PostGIS
- Why PostGIS: enables spatial queries (ST_Contains/ST_Intersects), efficient indexing (GIST), and geospatial types for waters/reaches/claims.
- Geometry types:
  - `WaterBody.geometry`: MULTIPOLYGON (SRID 4326), optional.
  - `Reach.geometry`: MULTIPOLYGON (SRID 4326), optional; represents claimable reach geometry.
  - Claims reference reaches; catches reference reaches and water bodies.
- Indexing: add GIST indexes on geometry columns in migrations for fast intersects/contains queries, e.g.:
  - `CREATE INDEX idx_waters_geom_gist ON waters USING GIST (geometry);`
  - `CREATE INDEX idx_reaches_geom_gist ON reaches USING GIST (geometry);`
- Query patterns: use `ST_Intersects`/`ST_Contains` between reach polygons and catch points; consider bounding boxes for coarse filtering before precise intersects.

## Map / API shape
- Endpoint: `GET /api/map/state` → 
```json
{
  "waters": [{ "id": 1, "name": "Demo Creek", "region": "Demo" }],
  "reaches": [
    {
      "id": 1,
      "water_body_id": 1,
      "name": "Reach 1",
      "geometry_wkt": "...",
      "geometry_geojson": { "type": "Polygon", "coordinates": [...] },
      "active_claim": {
        "id": 10,
        "user_id": "demo-user",
        "status": "active",
        "expires_at": "..."
      }
    }
  ]
}
```
- Geometry encoding: both WKT and GeoJSON (GeoJSON preferred for map layers).
- Active claim (if any): includes `id`, `user_id`, `status`, `expires_at`.

## Auth / user placeholder
- No full auth in this pass; claims use `X-User-Id` header (defaults to `test-user`) via `get_current_user_id` dependency.
- Legacy JWT deps remain for future real auth; current claim endpoints rely on header only.

## Error responses
- Claim conflicts: `409` with `detail: "Reach already claimed"` (header `X-Error-Code: CLAIM_CONFLICT`).
- Missing reach: `404` with `detail: "Reach not found"` (header `X-Error-Code: REACH_NOT_FOUND`).
- Other endpoints follow FastAPI defaults; normalize codes as more rules are added.

## Stats & leaderboard
- Endpoint: `GET /api/stats/claims` → `{ leaders: [{ user_id, active_claims }, ...] }` (active claims only).

## Demo data & seeding
- Script: `scripts/seed_demo_data.py`
- Usage: `cd backend && source .venv/bin/activate && python scripts/seed_demo_data.py`
- Behavior: seeds a demo water ("Demo Creek") and 3 reaches with simple geometries if none exist (skip if present; `--reset-demo` to recreate).
- Assumes reachable DB with PostGIS enabled; geometry omitted if not on Postgres.

## Tests
```bash
cd path/to/fishclaim-backend
source .venv/bin/activate
pip install pytest
pytest
```
- Tests include health, water/reach listing, claims (`tests/test_claims.py`), stats (`tests/test_stats.py`), and seeding helper (`tests/test_seed_demo.py`); SQLite config is set in tests (env vars) to allow fast runs. Extend with domain-specific cases as features grow.

## Session log helper
- Log file: `docs/FISHCLAIM_SESSION_LOG.md`
- Helper: `scripts/append_session_log.sh`
- Usage: `bash scripts/append_session_log.sh "what you did"` (defaults user to Conor; adds timestamp).

## Patterns / notes
- Claims: `evaluate_claim_for_catch` deactivates prior active claim per zone/species if a larger fish is logged; enforces unique active claim (DB constraint).
- Request correlation: middleware adds `X-Request-ID` per request.
- DB: models are simple, no migrations yet; ensure Postgres/PostGIS available before running.

## Quick start for new devs
1) Clone repos into `<path>`.  
2) Backend: create venv, install requirements, configure `.env`, run `uvicorn app.main:app --reload`.  
3) DB: ensure Postgres/PostGIS reachable (`DATABASE_URL`); create `fishclaim_default` network if using compose.
4) Compose option: `docker compose up -d --build backend` (after `.env` and network).
5) Frontend: see frontend README for `npm install && npm run dev -- --host --port 5173`; set `VITE_API_BASE_URL`.
6) Dev logs live at `docs/FISHCLAIM_SESSION_LOG.md`; append via `scripts/append_session_log.sh`.
