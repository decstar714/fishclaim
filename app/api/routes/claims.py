from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.models import ClaimStatus
from app.services.claims import expire_stale_claims

router = APIRouter(prefix="/claims", tags=["claims"])


def evaluate_claim_for_catch(db: Session, catch: models.Catch):
    expire_stale_claims(db)
    current_claim: models.Claim | None = (
        db.query(models.Claim)
        .filter(
            models.Claim.reach_id == catch.reach_id,
            models.Claim.species_id == catch.species_id,
            models.Claim.status == ClaimStatus.ACTIVE.value,
        )
        .one_or_none()
    )

    if current_claim and current_claim.length_cm >= catch.length_cm:
        return

    if current_claim:
        current_claim.status = ClaimStatus.EXPIRED.value

    new_claim = models.Claim(
        user_id=str(catch.user_id),
        water_body_id=catch.water_body_id,
        reach_id=catch.reach_id,
        species_id=catch.species_id,
        catch_id=catch.id,
        length_cm=catch.length_cm,
        status=ClaimStatus.ACTIVE.value,
        expires_at=datetime.utcnow() + timedelta(hours=72),
    )
    db.add(new_claim)
    db.commit()


@router.post("/", response_model=schemas.Claim, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: schemas.ClaimCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    expire_stale_claims(db)
    reach_id = payload.reach_id
    note = payload.note
    ttl_hours = payload.ttl_hours or 72

    reach = db.query(models.Reach).get(reach_id)
    if not reach:
        raise HTTPException(status_code=404, detail="Reach not found", headers={"X-Error-Code": "REACH_NOT_FOUND"})

    existing = (
        db.query(models.Claim)
        .filter(
            models.Claim.reach_id == reach_id,
            models.Claim.status == ClaimStatus.ACTIVE.value,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Reach already claimed", headers={"X-Error-Code": "CLAIM_CONFLICT"})

    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    claim = models.Claim(
        user_id=str(user_id),
        water_body_id=reach.water_body_id,
        reach_id=reach.id,
        species_id=None,  # optional until species is modeled per claim
        catch_id=None,  # optional: claim without catch context for now
        length_cm=0.0,
        status=ClaimStatus.ACTIVE.value,
        expires_at=expires_at,
        note=note,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@router.get("/reach/{reach_id}", response_model=list[schemas.Claim])
def get_reach_claims(reach_id: int, db: Session = Depends(get_db)):
    expire_stale_claims(db)
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.reach_id == reach_id)
        .order_by(models.Claim.created_at.desc())
        .all()
    )
    return claims


@router.get("/me", response_model=list[schemas.Claim])
def get_my_claims(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    expire_stale_claims(db)
    claims = (
        db.query(models.Claim)
        .filter(
            models.Claim.user_id == str(user_id),
            models.Claim.status == ClaimStatus.ACTIVE.value,
        )
        .order_by(models.Claim.created_at.desc())
        .all()
    )
    return claims
