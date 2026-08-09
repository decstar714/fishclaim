import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from app.main import create_app  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app import models  # noqa: E402
from app.services.claims import expire_stale_claims  # noqa: E402


def setup_module(_module=None):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        water = models.WaterBody(name="Test River", region="Test Region")
        db.add(water)
        db.flush()
        reach = models.Reach(
            water_body_id=water.id,
            name="Test Reach",
            description="Demo reach",
            order_index=1,
        )
        db.add(reach)
        db.commit()


def test_create_claim_and_conflict():
    client = TestClient(create_app())
    payload = {"reach_id": 1, "note": "first"}
    resp = client.post("/api/claims/", json=payload, headers={"X-User-Id": "u1"})
    assert resp.status_code == 201, resp.text

    # second claim on same reach should conflict while active
    resp2 = client.post("/api/claims/", json=payload, headers={"X-User-Id": "u1"})
    assert resp2.status_code == 409


def test_expire_helper_marks_claims():
    with SessionLocal() as db:
        claim = (
            db.query(models.Claim)
            .filter(models.Claim.reach_id == 1)
            .first()
        )
        claim.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        updated = expire_stale_claims(db)
        assert updated >= 1
        refreshed = db.query(models.Claim).get(claim.id)
        assert refreshed.status == models.ClaimStatus.EXPIRED.value
