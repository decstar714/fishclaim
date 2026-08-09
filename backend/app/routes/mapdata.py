"""Geometry for the map.

Both endpoints take a viewport bbox and return only what falls inside it, which
is what lets the client refetch on every pan without dragging the whole river
across the wire each time.

Filtering happens in Python, on a bounding box computed from the stored
GeoJSON. That is honest about what this is: with a river's worth of reaches it
costs nothing. It stops being reasonable somewhere around a few thousand rows,
and that is the point at which the geometry wants to be a real PostGIS column
with a GIST index rather than a text blob -- not before.
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from .claims import _expire_if_needed

router = APIRouter(tags=["mapdata"])


def _bounds(geometry: dict) -> tuple[float, float, float, float] | None:
    coords = geometry.get("coordinates") or []
    if geometry.get("type") == "MultiLineString":
        coords = [pt for part in coords for pt in part]
    if not coords:
        return None
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _overlaps(geometry: dict, box: tuple | None) -> bool:
    if box is None:
        return True
    b = _bounds(geometry)
    if b is None:
        return False
    minx, miny, maxx, maxy = b
    bminx, bminy, bmaxx, bmaxy = box
    return not (maxx < bminx or minx > bmaxx or maxy < bminy or miny > bmaxy)


def _box(minX, minY, maxX, maxY):
    if None in (minX, minY, maxX, maxY):
        return None
    return (minX, minY, maxX, maxY)


def _zones_with_geometry(db: Session):
    return (
        db.query(models.Zone)
        .filter(models.Zone.geometry_geojson.isnot(None))
        .all()
    )


@router.get("/rivers")
def rivers(
    db: Session = Depends(get_db),
    minX: float | None = None,
    minY: float | None = None,
    maxX: float | None = None,
    maxY: float | None = None,
):
    """Every zone that has geometry, as GeoJSON. This is the water itself."""
    box = _box(minX, minY, maxX, maxY)
    features = []
    for zone in _zones_with_geometry(db):
        geometry = json.loads(zone.geometry_geojson)
        if not _overlaps(geometry, box):
            continue
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "zone_id": zone.id,
                "name": zone.name,
                "comid": zone.comid,
                "water_id": zone.water_id,
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/claims")
def claims_bbox(
    db: Session = Depends(get_db),
    minX: float | None = None,
    minY: float | None = None,
    maxX: float | None = None,
    maxY: float | None = None,
):
    """Held water only, carrying the geometry of the zone it covers.

    A claim has no shape of its own -- it borrows the reach it was won on. That
    is the whole reason zones needed geometry before this could mean anything.
    """
    box = _box(minX, minY, maxX, maxY)
    by_zone = {z.id: z for z in _zones_with_geometry(db)}
    if not by_zone:
        return {"claims": []}

    rows = (
        db.query(models.Claim)
        .filter(models.Claim.is_active.is_(True),
                models.Claim.zone_id.in_(by_zone.keys()))
        .all()
    )

    # Reads are when a claim finds out it is dead -- there is no sweeper.
    if any(_expire_if_needed(c) for c in rows):
        db.commit()
        rows = [c for c in rows if c.is_active]

    species = {s.id: s.common_name for s in db.query(models.Species).all()}

    out = []
    for claim in rows:
        zone = by_zone[claim.zone_id]
        geometry = json.loads(zone.geometry_geojson)
        if not _overlaps(geometry, box):
            continue
        out.append({
            "claim_id": claim.id,
            "zone_id": zone.id,
            "zone_name": zone.name,
            "user_id": claim.user_id,
            "species_id": claim.species_id,
            "species": species.get(claim.species_id),
            "length_cm": claim.length_cm,
            "geometry": geometry,
        })
    return {"claims": out}
