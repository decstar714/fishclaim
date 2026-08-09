from fastapi import APIRouter, Depends
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from app import models
from app.models import ClaimStatus
from app.core.database import get_db

router = APIRouter(prefix="/map", tags=["map"])


def to_geojson(geom):
    if geom is None:
        return None
    try:
        return mapping(to_shape(geom))
    except Exception:
        return None


@router.get("/state")
def map_state(db: Session = Depends(get_db)):
    waters = db.query(models.WaterBody).all()
    reaches = db.query(models.Reach).all()
    reaches_out = []
    for reach in reaches:
        active_claim = (
            db.query(models.Claim)
            .filter(
                models.Claim.reach_id == reach.id,
                models.Claim.status == ClaimStatus.ACTIVE.value,
            )
            .order_by(models.Claim.created_at.desc())
            .first()
        )
        reaches_out.append(
            {
                "id": reach.id,
                "water_body_id": reach.water_body_id,
                "name": reach.name,
                "description": reach.description,
                "geometry_wkt": to_shape(reach.geometry).wkt if reach.geometry else None,
                "geometry_geojson": to_geojson(reach.geometry),
                "active_claim": {
                    "id": active_claim.id,
                    "user_id": active_claim.user_id,
                    "status": active_claim.status,
                    "expires_at": active_claim.expires_at.isoformat() if active_claim.expires_at else None,
                }
                if active_claim
                else None,
            }
        )
    return {
        "waters": [{"id": w.id, "name": w.name, "region": w.region} for w in waters],
        "reaches": reaches_out,
    }
