#!/usr/bin/env python3
"""Fill a water's zones with real river geometry from USGS.

Zones started life as ordered records with names and no shape, which is why the
map renders a basemap and nothing else. There is no need to invent the geometry:
USGS has already segmented every stream in the country into *reaches*, each with
a stable identifier (COMID) and a LineString. This pulls them.

Why reaches rather than a hex grid: the games this borrows from -- Pokemon GO's
S2 cells, Run An Empire's tiles -- claim **area**, because a city is an area. A
river is a line. Drop a hex grid on the South Branch and most cells are pasture
with a thread of water through one corner. A reach is the unit anglers already
think in, and it comes pre-drawn.

    # see what a river is made of, without touching the database
    python scripts/ingest_nhd.py --start -74.8517 40.7178 --km 25 --dry-run

    # create zones for the 25km below Ken Lockwood Gorge
    python scripts/ingest_nhd.py --start -74.8517 40.7178 --km 25 --water 1

    # attach geometry to zones that already exist, by name
    python scripts/ingest_nhd.py --start -74.8517 40.7178 --km 25 --water 1 --match-existing

Re-running is safe: reaches are keyed on COMID, so an existing zone is updated
rather than duplicated.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

NLDI = "https://api.water.usgs.gov/nldi/linked-data/comid"
UA = {"User-Agent": "fishclaim-ingest/1.0 (+https://github.com/decstar714/fishclaim)"}


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def comid_at(lon: float, lat: float) -> str:
    """Which reach is this point on?"""
    q = urllib.parse.quote(f"POINT({lon} {lat})", safe="")
    data = get_json(f"{NLDI}/position?coords={q}&f=json")
    feats = data.get("features") or []
    if not feats:
        raise SystemExit(f"no NHD reach found at {lon},{lat} -- is that point on water?")
    return str(feats[0]["properties"]["comid"])


def reaches_from(comid: str, km: float, direction: str) -> list[dict]:
    """Walk the mainstem from a reach and return each reach with its geometry."""
    url = f"{NLDI}/{comid}/navigation/{direction}/flowlines?distance={km}&f=json"
    out = []
    for f in get_json(url).get("features", []):
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if geom.get("type") == "MultiLineString":
            coords = [pt for part in coords for pt in part]
            geom = {"type": "LineString", "coordinates": coords}
        if not coords:
            continue
        out.append({
            "comid": str(f["properties"].get("nhdplus_comid") or f["properties"].get("comid")),
            "geometry": geom,
            "vertices": len(coords),
        })
    return out


def length_km(coords: list) -> float:
    """Rough great-circle length. Good enough to label a reach."""
    from math import radians, sin, cos, asin, sqrt
    total = 0.0
    for (lon1, lat1, *_), (lon2, lat2, *_) in zip(coords, coords[1:]):
        dlon, dlat = radians(lon2 - lon1), radians(lat2 - lat1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        total += 2 * asin(sqrt(a)) * 6371.0
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", nargs=2, type=float, metavar=("LON", "LAT"), required=True,
                    help="a point on the river to start from")
    ap.add_argument("--km", type=float, default=20.0, help="how far to walk (default 20)")
    ap.add_argument("--direction", default="DM", choices=["DM", "UM"],
                    help="DM = downstream mainstem, UM = upstream (default DM)")
    ap.add_argument("--water", type=int, help="water_id to attach zones to")
    ap.add_argument("--dry-run", action="store_true", help="print what would happen")
    ap.add_argument("--match-existing", action="store_true",
                    help="attach geometry to existing zones in order instead of creating new ones")
    args = ap.parse_args()

    lon, lat = args.start
    print(f"finding the reach at {lon}, {lat} ...")
    start = comid_at(lon, lat)
    print(f"  COMID {start}")

    print(f"walking {args.direction} for {args.km} km ...")
    reaches = reaches_from(start, args.km, args.direction)
    if not reaches:
        raise SystemExit("no reaches returned")

    total = sum(length_km(r["geometry"]["coordinates"]) for r in reaches)
    print(f"  {len(reaches)} reaches, {total:.1f} km of water\n")
    for i, r in enumerate(reaches[:6], 1):
        km = length_km(r["geometry"]["coordinates"])
        print(f"    {i:2}. COMID {r['comid']:>9}  {km:5.2f} km  {r['vertices']:3} vertices")
    if len(reaches) > 6:
        print(f"    ... and {len(reaches) - 6} more")

    if args.dry_run:
        print("\ndry run -- nothing written")
        return 0

    if not args.water:
        raise SystemExit("\n--water is required unless --dry-run")

    os.environ.setdefault("DATABASE_URL", "sqlite:///./fishclaim.db")
    from sqlalchemy import inspect, text  # noqa: E402
    from app.database import Base, SessionLocal, engine  # noqa: E402
    from app import models  # noqa: E402

    Base.metadata.create_all(bind=engine)

    # create_all creates missing tables but never ALTERs an existing one, so a
    # database that predates these two columns will not gain them. Add them here
    # rather than making someone read a traceback about a missing column. This
    # is the seam where the project wants Alembic.
    cols = {c["name"] for c in inspect(engine).get_columns("zones")}
    with engine.connect() as conn:
        for col, ddl in (("comid", "VARCHAR"), ("geometry_geojson", "TEXT")):
            if col not in cols:
                conn.execute(text(f"ALTER TABLE zones ADD COLUMN {col} {ddl}"))
                conn.commit()
                print(f"  added missing column zones.{col}")

    db = SessionLocal()
    water = db.get(models.Water, args.water)
    if not water:
        raise SystemExit(f"no water with id {args.water}")

    created = updated = 0
    if args.match_existing:
        zones = (db.query(models.Zone)
                   .filter_by(water_id=water.id)
                   .order_by(models.Zone.order_index)
                   .all())
        print(f"\nattaching geometry to {len(zones)} existing zones on {water.name}")
        for zone, reach in zip(zones, reaches):
            zone.comid = reach["comid"]
            zone.geometry_geojson = json.dumps(reach["geometry"])
            updated += 1
            print(f"    {zone.name} <- COMID {reach['comid']}")
    else:
        print(f"\nwriting {len(reaches)} zones to {water.name}")
        for i, reach in enumerate(reaches):
            zone = (db.query(models.Zone)
                      .filter_by(water_id=water.id, comid=reach["comid"])
                      .one_or_none())
            km = length_km(reach["geometry"]["coordinates"])
            if zone:
                updated += 1
            else:
                zone = models.Zone(water_id=water.id,
                                   name=f"Reach {i + 1} ({reach['comid']})",
                                   order_index=i)
                db.add(zone)
                created += 1
            zone.comid = reach["comid"]
            zone.geometry_geojson = json.dumps(reach["geometry"])
            zone.description = f"NHD reach {reach['comid']}, {km:.2f} km"

    db.commit()
    db.close()
    print(f"\ndone -- {created} created, {updated} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
