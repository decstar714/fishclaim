from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .. import models, schemas
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/claims", tags=["claims"])
settings = get_settings()


def _compute_expires_at(claim: models.Claim) -> datetime:
    lifetime = timedelta(days=settings.claim_lifetime_days)
    return claim.created_at + lifetime


def _expire_if_needed(claim: models.Claim | None) -> bool:
    """Return True if claim is expired and was marked inactive."""
    if not claim:
        return False
    if _compute_expires_at(claim) < datetime.utcnow():
        claim.is_active = False
        return True
    return False


def evaluate_claim_for_catch(db: Session, catch: models.Catch):
    current_claim: models.Claim | None = (
        db.query(models.Claim)
        .filter(
            models.Claim.zone_id == catch.zone_id,
            models.Claim.species_id == catch.species_id,
            models.Claim.is_active == True,
        )
        .one_or_none()
    )

    if _expire_if_needed(current_claim):
        db.commit()
        current_claim = None

    # If the same user already holds the claim, refresh its timestamp and update length if better.
    if current_claim and current_claim.user_id == catch.user_id:
        current_claim.created_at = datetime.utcnow()
        if catch.length_cm > current_claim.length_cm:
            current_claim.length_cm = catch.length_cm
        db.commit()
        return

    # If another user's claim exists and is longer, keep it.
    if current_claim and current_claim.length_cm >= catch.length_cm:
        return

    # Transfer claim to new user (or first claim)
    if current_claim:
        current_claim.is_active = False

    db.add(
        models.Claim(
            user_id=catch.user_id,
            water_id=catch.water_id,
            zone_id=catch.zone_id,
            species_id=catch.species_id,
            catch_id=catch.id,
            length_cm=catch.length_cm,
            is_active=True,
        )
    )
    db.commit()


@router.get("/zone/{zone_id}", response_model=list[schemas.Claim])
def get_zone_claims(zone_id: int, db: Session = Depends(get_db)):
    claims = (
        db.query(models.Claim)
        .filter(
            and_(
                models.Claim.zone_id == zone_id,
                models.Claim.is_active == True,
            )
        )
        .all()
    )

    # Populate expires_at for clients
    for claim in claims:
        claim.expires_at = _compute_expires_at(claim)

    # Mark expired claims inactive on read
    expired = False
    for claim in claims:
        if _expire_if_needed(claim):
            expired = True
    if expired:
        db.commit()
        claims = (
            db.query(models.Claim)
            .filter(
                and_(
                    models.Claim.zone_id == zone_id,
                    models.Claim.is_active == True,
                )
            )
            .all()
        )
        for claim in claims:
            claim.expires_at = _compute_expires_at(claim)

    return claims
