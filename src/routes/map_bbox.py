# routes/map_bbox.py
from fastapi import APIRouter, Query
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["map-bbox"])

def empty_fc() -> Dict[str, Any]:
    return {"type": "FeatureCollection", "features": []}

@router.get("/rivers")
def rivers_by_bbox(
    minX: float = Query(...),
    minY: float = Query(...),
    maxX: float = Query(...),
    maxY: float = Query(...),
):
    # TODO: implement real query; for now return empty to avoid 404s
    return empty_fc()

@router.get("/claims")
def claims_by_bbox(
    minX: float = Query(...),
    minY: float = Query(...),
    maxX: float = Query(...),
    maxY: float = Query(...),
):
    # TODO: implement real query; for now return empty list wrapper
    return {"claims": []}
