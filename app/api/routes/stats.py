from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.models import ClaimStatus

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/claims")
def claim_stats(db: Session = Depends(get_db)):
    q = (
        db.query(
            models.Claim.user_id.label("user_id"),
            func.count(models.Claim.id).label("active_claims"),
        )
        .filter(models.Claim.status == ClaimStatus.ACTIVE.value)
        .group_by(models.Claim.user_id)
        .order_by(func.count(models.Claim.id).desc())
    )
    leaders = [{"user_id": row.user_id, "active_claims": row.active_claims} for row in q.all()]
    return {"leaders": leaders}
