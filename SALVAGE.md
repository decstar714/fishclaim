# Salvage notes

Written 2026-08-08, when this branch was recovered from the homelab. The commit
before this one is the working tree exactly as it stood there on 2025-11-28,
untouched. Everything below is what I found trying to run it.

## Read this first

`docs/FISHCLAIM_SESSION_LOG.md` is a dated log of what was built here and why.
It is the only record of the reasoning, and it explains decisions that look
wrong without it — most importantly that `Claim.user_id` is a `String` on
purpose, because `app/api/deps.py` reads an `X-User-Id` header and falls back to
`"test-user"`. Auth is a deliberate v0 placeholder on this branch, not a bug.

## The tests do not run as configured

Six of the seven need PostGIS and are pointed at SQLite:

```
tests/test_health.py      1 passed
tests/test_waters.py      2 errors
tests/test_claims.py      2 errors
tests/test_stats.py       1 error
tests/test_seed_demo.py   1 error
```

Every failure is the same one. Each test module does

```python
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
```

and `create_all` then tries to build `reaches.geometry`, a
`Geometry("MULTIPOLYGON", srid=4326)` column. SQLite has no geometry type
without SpatiaLite, so the `CREATE TABLE` fails with an `OperationalError` on
`('reaches', 'geometry')`. Only the health test avoids it, because it never
touches a spatial table.

The fix is to point the tests at the PostGIS service in `docker-compose.yml`
rather than SQLite. `test_health` is the only one that is honestly passing
today, and CI would have shown this — but CI was broken on `main` for unrelated
reasons and this branch never ran it either.

## `CORS_ORIGINS` cannot be a comma-separated string here

`app/core/config.py` declares

```python
cors_origins: List[str] = Field(...)
```

with a `@field_validator(..., mode="before")` meant to split a comma-separated
value. That validator never runs. For a complex field type, pydantic-settings
JSON-decodes the dotenv value *at the source*, before validators, so a `.env`
containing

```
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

— which is exactly what this branch's own `.env.example` documents — dies with

```
SettingsError: error parsing value for field "cors_origins" from source "DotEnvSettingsSource"
```

and the app never starts. Passing it as an environment variable instead of a
dotenv key works, which is why compose was fine and nobody noticed.

`main` does not have this problem: it declares the field as
`list[str] | str`, and the union stops pydantic-settings treating it as
purely complex, so the raw string reaches the validator. Copying that union
across is the one-line fix.

## What is worth lifting

- The PostGIS setup, whole: `postgis/postgis:16-3.4` with a healthcheck and a
  named volume, `geoalchemy2` + `shapely`, and `Geometry("MULTIPOLYGON",
  srid=4326)` on waters and reaches. `main` still has no geometry layer.
- The layout: `create_app()`, `app/core`, `app/api`, `app/services`, `init_db()`
  on startup instead of `create_all` at import, and the request-ID middleware.
- `/reaches`, `/stats/claims`, `/map/state`.
- `scripts/seed_demo_data.py` — Demo Creek with three polygon reaches, which is
  the only thing here that produces real geometry to look at.

## What must not come across

- The claim rules. This branch has `__table_args__ = ()` and reads the active
  claim with `.one_or_none()`, so nothing at the schema level stops two active
  claims existing for a reach. `main` has the partial unique index and the
  reasoning for it written down in `app/models.py`. Keep `main`'s.
- The expiry model. 72 hours is hardcoded in two places here;
  `main` computes it from `CLAIM_LIFETIME_DAYS`.
- Anything that would drop `sessions`. This branch predates the sessions table
  and `/api/sessions` entirely — holding a zone by logging time on the water is
  half the game and does not exist here.
