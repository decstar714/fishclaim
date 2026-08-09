# FishClaim — API

Backend for FishClaim, a territory game played on real rivers. The biggest fish caught in a
stretch of water holds that stretch, until somebody catches a bigger one or the holder stops
showing up and the claim decays. This repo is the **FastAPI service** — the UI lives in
[`fishclaim`](https://github.com/decstar714/fishclaim).

**Stack:** FastAPI · SQLAlchemy 2.0 · PostgreSQL 15 · Docker Compose

![Status](https://img.shields.io/badge/status-mvp-yellow) ![License](https://img.shields.io/badge/license-private-lightgrey)

---

## Table of Contents

- [The rule](#the-rule)
- [Data model](#data-model)
- [API reference](#api-reference)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Secrets](#secrets)
- [Seeding the database](#seeding-the-database)
- [Deployment](#deployment)
- [Project structure](#project-structure)
- [Branching](#branching)
- [Status](#status)

---

## The rule

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

That lives in `evaluate_claim_for_catch` in `app/routes/claims.py`, and it is the only place a
claim is ever awarded. Three consequences are worth internalising before changing anything.

**Claims decay.** A claim expires `CLAIM_LIFETIME_DAYS` after it was last refreshed. The holder
refreshes it by catching again, or by logging time on the water (`POST /api/sessions`) without
catching anything. You have to keep showing up to hold water, which is the point of the game.

**Beaten claims are kept, not deleted.** They stay as rows with `is_active=false`, so a zone has
a history rather than only a current holder. That history is why the uniqueness rule is a
**partial** unique index on `(zone_id, species_id) WHERE is_active` — a plain unique constraint
including `is_active` would also cap you at one *inactive* row per zone, and the third time a
claim changed hands in any zone the insert would die with an `IntegrityError`. That is the core
loop of the game, so it broke everywhere at once. See the comment in `app/models.py`.

**Expiry is lazy, not scheduled.** Nothing sweeps the table. A claim is only noticed to be dead
when someone reads that zone or logs a catch in it — `_expire_if_needed` flips the row then.
There is no cron and no background task, so a zone nobody visits keeps a stale `is_active=true`
row in the database until the next request touches it. Query the table directly and you will see
claims that the API would consider expired.

---

## Data model

```mermaid
erDiagram
    USER  ||--o{ CATCH   : logs
    USER  ||--o{ CLAIM   : holds
    USER  ||--o{ SESSION : fishes
    WATER ||--o{ ZONE    : "divided into"
    ZONE  ||--o{ CATCH   : "caught in"
    ZONE  ||--o{ CLAIM   : "claimed by"
    ZONE  ||--o{ SESSION : "fished in"
    SPECIES ||--o{ CATCH : "of"
    CATCH ||--o| CLAIM   : "backs"

    CATCH   { float length_cm float lat float lng datetime caught_at }
    CLAIM   { float length_cm bool is_active datetime created_at datetime revoked_at }
    SESSION { int duration_minutes float best_length_cm datetime started_at }
    ZONE    { int order_index string name }
```

| Table | Holds |
|---|---|
| `users` | Account, hashed password, display name |
| `waters` | A river or lake — name, type, region |
| `zones` | An ordered stretch of a water. Claims are per zone, not per water |
| `species` | Common + scientific name, category |
| `catches` | A fish: length, optional weight, `lat`/`lng`, method, notes, photo URL |
| `claims` | Who holds a zone+species, backed by the catch that earned it |
| `sessions` | Time on the water. Refreshes a claim without a catch |

A claim always points at the `catch` that earned it, so "who holds this pool, and with what fish"
is answerable without recomputing anything.

**`claims.created_at` is not creation time.** Refreshing a claim overwrites it with `utcnow()`,
because expiry is computed as `created_at + CLAIM_LIFETIME_DAYS`. It means *last refreshed*. The
column is misnamed and worth renaming the next time the schema moves.

There is no geometry layer — no PostGIS, no GeoAlchemy2, no `ST_` calls. Positions are plain
`lat`/`lng` floats on a catch, and zones are ordered records rather than polygons. Zone
boundaries and point-in-polygon claim resolution are the features that would make PostGIS worth
adding; until then it would be weight without a job.

---

## API reference

All routes are mounted under `/api`. Interactive docs at `/api/docs` once the server is up.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/health` | — | Liveness check |
| `POST` | `/api/auth/register` | — | Create an account |
| `POST` | `/api/auth/login` | — | Form-encoded login, returns a bearer token |
| `GET` | `/api/waters/` | — | List waters |
| `GET` | `/api/waters/{water_id}/zones` | — | Zones of a water, in `order_index` order |
| `GET` | `/api/species/` | — | List species |
| `POST` | `/api/catches/` | **yes** | Log a catch. Runs claim evaluation |
| `GET` | `/api/claims/zone/{zone_id}` | — | Active claims in a zone, with `expires_at` |
| `POST` | `/api/sessions/` | **yes** | Log time on the water. Can refresh a claim |
| `GET` | `/api/sessions/` | **yes** | Your own sessions |
| `GET` | `/api/rivers` | — | Placeholder — returns empty GeoJSON |
| `GET` | `/api/claims` | — | Placeholder — returns empty GeoJSON |

Auth is a bearer JWT from `/api/auth/login`, signed HS256, validated in `app/deps.py`. Login
takes `application/x-www-form-urlencoded` (it is FastAPI's `OAuth2PasswordRequestForm`), not
JSON — a JSON login body returns 422.

`/api/rivers` and `/api/claims` accept `minX`/`minY`/`maxX`/`maxY` and ignore them. They exist so
the map client gets a valid empty response instead of a 404 while there is no geometry to serve.

---

## Quick start

### Docker

```bash
cp .env.example .env          # then set SECRET_KEY -- see Secrets
docker compose up -d --build
```

API on `http://localhost:8080/api`, Postgres on `:5432`, docs at `/api/docs`.
Override the API port with `BACKEND_PORT`.

### Local Python

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: ./.venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY and DATABASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You still need a Postgres to point `DATABASE_URL` at. The quickest is the compose database on
its own:

```bash
docker compose up -d db
```

### Running the UI alongside

Clone [`fishclaim`](https://github.com/decstar714/fishclaim) next to this repo, make sure
`CORS_ORIGINS` here includes the Vite dev host (`http://localhost:5173` is the default), and
point the UI's `VITE_API_BASE_URL` at `http://localhost:8080/api`. Read [Status](#status) first —
the two `main` branches do not currently agree on the API.

---

## Configuration

Everything is read from the environment, or from `.env` in the repo root.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | *required* | SQLAlchemy URL, e.g. `postgresql+psycopg2://user:password@db:5432/fishclaim` |
| `SECRET_KEY` | *required* | JWT signing key. Validated at startup — see [Secrets](#secrets) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime |
| `CLAIM_LIFETIME_DAYS` | `30` | How long a claim survives without a refresh |
| `CORS_ORIGINS` | localhost dev ports | Comma-separated list of allowed origins |
| `BACKEND_PORT` | `8080` | Host port compose publishes. Read by compose, not by the app |
| `SEED_USER_*`, `SEED_FORCE_RESET` | — | Read by `app/seed.py` only |

`Settings` sets `extra="ignore"` deliberately. The last four rows are consumed by compose and by
the seed script rather than by the app, and without `extra="ignore"` their presence in `.env` is
a hard startup failure — the documented local-Python path crashed on six keys the template
itself ships. Docker never hit it, because compose passes them as environment variables and
those are ignored either way.

---

## Secrets

Real values live in `.env`, which is gitignored. `.env.example` is the template and carries no
values. A new config key goes in both `.env.example` and the table above.

`SECRET_KEY` signs the JWTs, so it has to be a key nobody else has:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The app validates it at startup and refuses to boot on a blank, short, or placeholder value —
including `dev-secret-change-me`, which early commits used as a hardcoded default and which is
therefore readable by anyone in this repo's git log. Nothing else has ever been committed here:
no real key, no token, no database password. Changing the key invalidates every issued token, so
everyone logs in again.

A pre-commit scanner blocks credential-shaped strings before they can be staged. It is not
installed by cloning — hook it up once per checkout:

```bash
ln -sf ../../hooks/pre-commit .git/hooks/pre-commit
```

---

## Seeding the database

The seed creates the owner account, one water with two zones, and two species. It is idempotent:
existing rows are left alone, except the owner password when `SEED_FORCE_RESET=true`.

| | |
|---|---|
| Water | South Branch Raritan River (NJ) |
| Zones | Ken Lockwood Gorge · Califon to Cokesbury |
| Species | Brown Trout · Rainbow Trout |

```bash
python -m app.seed
# or, in Docker:
docker exec -it fishclaim_backend python -m app.seed
```

`SEED_USER_PASSWORD` has no default and the seed exits without one.

---

## Deployment

```bash
./deploy.sh [branch]      # default: main
```

Fetches the branch, rebuilds the backend image and restarts the backend container. It does not
touch the database container, so data survives a deploy.

| Container | Image | Port | Volume |
|---|---|---|---|
| `fishclaim_backend` | `python:3.12-slim` + FastAPI | `${BACKEND_PORT:-8080}` → 8000 | — |
| `fishclaim_db` | `postgres:15-alpine` | 5432 | `postgres_data` |

There are no migrations. `Base.metadata.create_all` runs at import in `app/main.py`, which
creates missing tables and **does not alter existing ones**. A column added to a model will
never appear in a database that already has that table — that is a manual `ALTER TABLE`, or a
dropped volume. Alembic is the fix whenever the schema starts moving in earnest.

The compose database uses `user`/`password` on a published port. That is fine on a laptop and
not fine on anything reachable.

---

## Project structure

```
fishclaim-backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, router wiring, create_all
│   ├── config.py            # Settings from env/.env, SECRET_KEY validation
│   ├── database.py          # Engine, SessionLocal, get_db dependency
│   ├── models.py            # SQLAlchemy tables + the partial unique index
│   ├── schemas.py           # Pydantic request/response models
│   ├── auth.py              # Password hashing, JWT minting
│   ├── deps.py              # get_current_user -- bearer token -> User
│   ├── seed.py              # Owner account, home water, zones, species
│   └── routes/
│       ├── health.py        # Liveness
│       ├── auth.py          # register, login
│       ├── waters.py        # Waters and their zones
│       ├── species.py       # Species list
│       ├── catches.py       # Log a catch -> triggers claim evaluation
│       ├── claims.py        # evaluate_claim_for_catch + zone claim reads
│       ├── sessions.py      # Time on the water, claim refresh
│       └── mapdata.py       # Placeholder GeoJSON endpoints
│
├── hooks/pre-commit         # Credential scanner (install it manually)
├── Dockerfile               # python:3.12-slim, uvicorn on :8000
├── docker-compose.yml       # backend + postgres:15-alpine
└── deploy.sh                # Pull, rebuild, restart -- leaves the db alone
```

---

## Branching

| Branch | Role |
|---|---|
| `main` | Stable |
| `dev` | Integration |
| `feature/*` | One branch per task |

---

## Status

**Working:** registration and login, waters and zones, species, catch logging, the full claim
lifecycle (take, refresh, decay, history), session logging, and the placeholder map endpoints.

**Known problems, in the order they will bite:**

**The UI on `dev` calls three endpoints this branch does not serve.** `GET /api/auth/me`,
`POST /api/auth/refresh` and `POST /api/claims/{id}/status` all return 404 here. They exist on
`feature/auth-session-hardening`, along with user roles, refresh-token rotation and a claim
review workflow — that branch was never merged and has no open PR. The visible symptom is that
login succeeds and the app immediately logs you back out, because the UI calls `/auth/me` right
after login and treats the 404 as a dead session. Either merge that branch or cut the calls out
of the UI; the two repos cannot both be right as they stand.

**`/api/auth/login` returns only an access token.** No refresh token, so the UI's rotation
logic never engages and a session simply ends when the token expires.

**There are no tests on this branch.** `tests/` exists only on `feature/auth-session-hardening`.
CI skips pytest when the directory is absent, so the build stays green without testing anything.

**No migrations.** See [Deployment](#deployment).

**Not built yet:** zone geometry, claim photos beyond a URL field, leaderboards, and anything
that needs to know a zone's shape rather than its order.
