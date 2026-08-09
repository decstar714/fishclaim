import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from app.main import create_app  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app import models  # noqa: E402
from app.models import ClaimStatus  # noqa: E402


def setup_module(_module=None):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        water = models.WaterBody(name="Stats River")
        db.add(water)
        db.flush()
        reach = models.Reach(water_body_id=water.id, name="Stats Reach")
        db.add(reach)
        claim = models.Claim(
            user_id="u1",
            water_body_id=water.id,
            reach_id=reach.id,
            length_cm=0.0,
            status=ClaimStatus.ACTIVE.value,
        )
        db.add(claim)
        db.commit()


def test_claim_stats():
    client = TestClient(create_app())
    resp = client.get("/api/stats/claims")
    assert resp.status_code == 200
    data = resp.json()
    assert data["leaders"][0]["user_id"] == "u1"
    assert data["leaders"][0]["active_claims"] == 1
