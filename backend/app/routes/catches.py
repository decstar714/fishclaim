from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .claims import evaluate_claim_for_catch
from ..deps import get_current_user


router = APIRouter(prefix="/catches", tags=["catches"])


@router.post("/", response_model=schemas.Catch)
def create_catch(
    catch_in: schemas.CatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # TEMP: until auth is in place, hardcode user_id 1
    user =  current_user

    zone = db.query(models.Zone).get(catch_in.zone_id)
    if not zone:
        raise HTTPException(status_code=400, detail="Zone not found")

    species = db.query(models.Species).get(catch_in.species_id)
    if not species:
        raise HTTPException(status_code=400, detail="Species not found")

    catch = models.Catch(
        user_id=user.id,
        water_id=catch_in.water_id,
        zone_id=catch_in.zone_id,
        species_id=catch_in.species_id,
        length_cm=catch_in.length_cm,
        weight_kg=catch_in.weight_kg,
        method=catch_in.method,
        notes=catch_in.notes,
        lat=catch_in.lat,
        lng=catch_in.lng,
    )
    db.add(catch)
    db.commit()
    db.refresh(catch)

    evaluate_claim_for_catch(db, catch)
    return catch

