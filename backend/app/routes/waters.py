from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/waters", tags=["waters"])


@router.get("/", response_model=list[schemas.Water])
def list_waters(db: Session = Depends(get_db)):
    return db.query(models.Water).all()


@router.get("/{water_id}/zones", response_model=list[schemas.Zone])
def list_zones_for_water(water_id: int, db: Session = Depends(get_db)):
    zones = (
        db.query(models.Zone)
        .filter(models.Zone.water_id == water_id)
        .order_by(models.Zone.order_index)
        .all()
    )
    return zones

