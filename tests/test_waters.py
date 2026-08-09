import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from app.main import create_app  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app import models  # noqa: E402


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


def test_list_waters():
    client = TestClient(create_app())
    resp = client.get("/api/waters")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test River"


def test_list_reaches():
    client = TestClient(create_app())
    resp = client.get("/api/reaches/water/1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Reach"
