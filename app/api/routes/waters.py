from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db

router = APIRouter(prefix="/waters", tags=["waters"])


@router.get("/", response_model=list[schemas.WaterBodyRead])
def list_waters(db: Session = Depends(get_db)):
    return db.query(models.WaterBody).all()


@router.get("/{water_id}", response_model=schemas.WaterBodyRead)
def get_water(water_id: int, db: Session = Depends(get_db)):
    water = db.query(models.WaterBody).get(water_id)
    if not water:
        raise HTTPException(status_code=404, detail="Water not found")
    return water
