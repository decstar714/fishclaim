# FishClaim Session Log

Purpose: chronological log of changes, decisions, todos, and open questions for the FishClaim backend. Append a new dated entry for each working session.

How to use this file:
- Append (don’t overwrite) a new section with timestamp, author (default "Conor"), summary of what you did, and next steps.
- Keep entries short and action-focused so future sessions can resume quickly.

## 2025-11-28T06:20:00+00:00 (Conor)
- Initialized session log and backend doc structure.
- Added helper script `scripts/append_session_log.sh` for quick log entries.
- See session notes in `docs/DEV_AGENT_SESSION_NOTES.md` for broader context.

## 2025-11-28T06:25:00+00:00 (Conor)
- Restructured backend to `app/core` (config, db, security) and `app/api/routes` (health, auth, waters, catches, claims) with request ID middleware.
- Added `.env.example` comments, updated README, backend docs, and quick start.
- Added session log helper script, session log file, pytest health test, and backend docs folder.
- Frontend README refreshed (Vite dev/build, API base var).
- TODO: set real DATABASE_URL/SECRET_KEY; ensure Postgres/PostGIS available; expand tests and map feature docs as features grow.

## 2025-11-28T06:40:00+00:00 (Conor)
- Hardened DB setup: compose now includes PostGIS service; `.env.example` documents real connection strings; backend uses `init_db` (PostGIS extension if available) and DB-aware health check.
- Spatial domain baseline: WaterBody + Reach (geometry), Claim/Catch updated to reference reaches; new reach endpoints (`/api/reaches/water/{id}`, `/api/reaches/{id}`); serializers emit WKT strings for geometry.
- Documentation: backend notes now include Database/Migrations section, Spatial design/PostGIS guidance, test updates.
- Tests: added reach/water list test (`tests/test_waters.py`), health test uses sqlite defaults.
- Frontend README: clarified map component location and API config notes.
- TODO: set real DB creds/SECRET_KEY; add GIST indexes via migrations later; flesh out spatial data loading and more domain tests; ensure PostGIS network `fishclaim_default` exists before compose up.

## 2025-11-28T07:05:00+00:00 (Conor)
- Implemented v0 claim rules: single active claim per reach, status/expiry/note, user from `X-User-Id` (defaults to test-user), lazy expiration helper. Endpoints: POST `/api/claims/`, GET `/api/claims/reach/{id}`, GET `/api/claims/me`.
- Map state endpoint `/api/map/state` returns reaches with WKT+GeoJSON and active claim. Frontend MapView now fetches and lists reaches/claims (stub UI).
- Added ClaimStatus, updated models/schemas to WaterBody/Reach/Claim/Catch relations, and DB helper handles PostGIS extension.
- Tests: new `tests/test_claims.py` for claim creation conflict + expiration helper; health/waters tests still pass with sqlite env.
- Docs updated: claim lifecycle, map/API shape, auth placeholder, testing notes. Frontend README adds Map & claims section.
- TODO: add real species/user auth later, spatial indexes/migrations, real geometries for reaches, and richer map rendering.

## 2025-11-28T06:40:12+00:00 (Conor)
- Added demo seeding script `scripts/seed_demo_data.py` (Demo Creek + 3 reaches with simple polygons; `--reset-demo` optional).
- Map API now returns waters + reaches with GeoJSON and active claims; stats endpoint `/api/stats/claims` added.
- Frontend MapView now renders polygons (Leaflet), click-to-claim with X-User-Id, and refreshes state; leaderboard component shows active claim counts.
- Tests: added `tests/test_stats.py` and `tests/test_seed_demo.py`; updated docs for map shape, stats, demo seeding, error responses.
- TODO: refine geometry loading, real auth/users, spatial indexes/migrations, improve map styling/claims UX.

## 2025-11-28T06:49:02+00:00 (root)
- PostGIS demo seed run; map/state + stats sanity checks; demo claims (demo-user-1 x2, demo-user-2 x1).
