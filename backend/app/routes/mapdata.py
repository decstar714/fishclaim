from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(tags=["mapdata"])


@router.get("/rivers")
def rivers(_: Session = Depends(get_db), minX: float | None = None, minY: float | None = None, maxX: float | None = None, maxY: float | None = None):
    # Placeholder empty GeoJSON to avoid 404s in the map client.
    return {"type": "FeatureCollection", "features": []}


@router.get("/claims")
def claims_bbox(_: Session = Depends(get_db), minX: float | None = None, minY: float | None = None, maxX: float | None = None, maxY: float | None = None):
    # Placeholder: no geometry stored yet. Return empty to suppress client errors.
    return {"claims": []}
