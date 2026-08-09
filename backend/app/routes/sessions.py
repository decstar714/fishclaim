from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])
settings = get_settings()


def _expire_claim_if_needed(claim: models.Claim | None) -> bool:
    """Return True if claim is expired and was marked inactive."""
    if not claim:
        return False
    lifetime = timedelta(days=settings.claim_lifetime_days)
    if claim.created_at + lifetime < datetime.utcnow():
        claim.is_active = False
        return True
    return False


@router.post("/", response_model=schemas.Session)
def create_session(
    session_in: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    zone = db.query(models.Zone).get(session_in.zone_id)
    if not zone or zone.water_id != session_in.water_id:
        raise HTTPException(status_code=400, detail="Zone or water not found")

    species = None
    if session_in.species_id:
        species = db.query(models.Species).get(session_in.species_id)
        if not species:
            raise HTTPException(status_code=400, detail="Species not found")

    session = models.Session(
        user_id=current_user.id,
        water_id=session_in.water_id,
        zone_id=session_in.zone_id,
        species_id=session_in.species_id,
        started_at=session_in.started_at or datetime.utcnow(),
        duration_minutes=session_in.duration_minutes,
        method=session_in.method,
        notes=session_in.notes,
        conditions=session_in.conditions,
        best_length_cm=session_in.best_length_cm,
    )
    db.add(session)

    # Refresh an existing claim for this user/zone/species if provided
    if session_in.species_id:
        active_claim: models.Claim | None = (
            db.query(models.Claim)
            .filter(
                models.Claim.zone_id == session.zone_id,
                models.Claim.species_id == session.species_id,
                models.Claim.is_active == True,
            )
            .one_or_none()
        )

        if _expire_claim_if_needed(active_claim):
            db.commit()
            active_claim = None

        if active_claim and active_claim.user_id == current_user.id:
            # Refresh timestamp and optionally improve length
            active_claim.created_at = datetime.utcnow()
            if (
                session_in.best_length_cm
                and session_in.best_length_cm > active_claim.length_cm
            ):
                active_claim.length_cm = session_in.best_length_cm

    db.commit()
    db.refresh(session)
    return session


@router.get("/", response_model=list[schemas.Session])
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sessions = (
        db.query(models.Session)
        .filter(models.Session.user_id == current_user.id)
        .order_by(models.Session.started_at.desc())
        .all()
    )
    return sessions
