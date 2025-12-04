from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/species", tags=["species"])


@router.get("/", response_model=list[dict])
def list_species(db: Session = Depends(get_db)):
    species = db.query(models.Species).all()
    return [  # keep simple shape for now
        {
            "id": s.id,
            "common_name": s.common_name,
            "scientific_name": s.scientific_name,
            "category": s.category,
        }
        for s in species
    ]
