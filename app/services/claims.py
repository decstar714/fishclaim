from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models
from app.models import ClaimStatus


def expire_stale_claims(db: Session) -> int:
    """Mark active claims as expired when past expires_at. Returns count updated."""
    now = datetime.utcnow()
    stale = (
        db.query(models.Claim)
        .filter(
            models.Claim.status == ClaimStatus.ACTIVE.value,
            models.Claim.expires_at != None,  # noqa: E711
            models.Claim.expires_at < now,
        )
        .all()
    )
    for claim in stale:
        claim.status = ClaimStatus.EXPIRED.value
    if stale:
        db.commit()
    return len(stale)


def default_expiry(hours: int | None = None) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours or 72)
