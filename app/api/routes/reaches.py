from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db

router = APIRouter(prefix="/reaches", tags=["reaches"])


@router.get("/{reach_id}", response_model=schemas.ReachRead)
def get_reach(reach_id: int, db: Session = Depends(get_db)):
    reach = db.query(models.Reach).get(reach_id)
    if not reach:
        raise HTTPException(status_code=404, detail="Reach not found")
    return reach


@router.get("/water/{water_body_id}", response_model=list[schemas.ReachRead])
def list_reaches_for_water(water_body_id: int, db: Session = Depends(get_db)):
    reaches = (
        db.query(models.Reach)
        .filter(models.Reach.water_body_id == water_body_id)
        .order_by(models.Reach.order_index)
        .all()
    )
    return reaches
