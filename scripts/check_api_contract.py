#!/usr/bin/env python3
"""Fail if the UI calls a route the API does not serve.

This is the check the two-repo split made impossible. The frontend spent months
calling `/auth/me`, `/auth/refresh` and `/claims/{id}/status` against a backend
that served none of them -- you could log in successfully and be thrown straight
back out, and no test anywhere had both halves in front of it at once.

It works by reading, not by running: every `${API_BASE}/...` template literal in
frontend/src is pulled out and compared against FastAPI's own route table. No
server, no database, no browser.

    python scripts/check_api_contract.py

Exit status is 0 when every called path resolves, 1 otherwise.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_SRC = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend"

# A call site looks like `${API_BASE}/waters/${water.id}/zones`. Grab everything
# up to the closing backtick or a query string.
CALL = re.compile(r"\$\{API_BASE\}(/[^`\"'?\s]*)")

# Any ${...} inside the path is an interpolated id. FastAPI writes the same
# thing as {water_id}; both become {} so they compare equal.
INTERP = re.compile(r"\$\{[^}]*\}")
PARAM = re.compile(r"\{[^}]*\}")


def normalise(path: str) -> str:
    path = INTERP.sub("{}", path)
    path = PARAM.sub("{}", path)
    # A trailing slash is not a different route to FastAPI's redirect handling,
    # and the UI is inconsistent about it. Compare without.
    return path.rstrip("/") or "/"


def called_paths() -> dict[str, list[str]]:
    """Every distinct path the UI calls, with the files that call it."""
    found: dict[str, list[str]] = {}
    for f in sorted(FRONTEND_SRC.rglob("*.js*")):
        for raw in CALL.findall(f.read_text()):
            found.setdefault(normalise(raw), []).append(
                str(f.relative_to(ROOT))
            )
    return found


def served_paths() -> set[str]:
    """Every path FastAPI actually mounts, minus the /api prefix.

    Read from the generated OpenAPI schema rather than by walking app.routes:
    newer FastAPI wraps included routers in objects with no `.path`, so walking
    the list silently yields nothing and the check passes when it should fail.
    The schema is the same thing /api/docs renders, and its shape is stable.
    """
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DATABASE_URL", "sqlite:///./contract-check.db")
    os.environ.setdefault(
        "SECRET_KEY", "contract-check-only-0123456789abcdefghij"
    )
    from app.main import app  # noqa: E402  -- needs the env set first

    return {
        normalise(p[len("/api"):])
        for p in app.openapi().get("paths", {})
        if p.startswith("/api")
    }


def main() -> int:
    calls = called_paths()
    served = served_paths()

    if not calls:
        print("no ${API_BASE} call sites found -- has the UI moved?")
        return 1

    missing = {p: files for p, files in calls.items() if p not in served}

    width = max(len(p) for p in calls)
    for path in sorted(calls):
        ok = path not in missing
        print(f"  {'ok ' if ok else 'MISSING'}  {path.ljust(width)}")

    print(f"\n{len(calls)} distinct paths called, {len(served)} served")

    if missing:
        print("\nThe UI calls routes the API does not serve:\n")
        for path, files in sorted(missing.items()):
            print(f"  {path}")
            for f in sorted(set(files)):
                print(f"      called from {f}")
        print(
            "\nEither add the route to backend/app/routes/, or stop calling it "
            "from the UI.\nThe two halves live in one repo so that this is one "
            "pull request."
        )
        return 1

    print("every route the UI calls exists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
