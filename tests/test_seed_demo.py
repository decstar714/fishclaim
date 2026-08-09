import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from app.core.database import Base, engine  # noqa: E402
from scripts.seed_demo_data import seed_demo  # noqa: E402
from app import models  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402


def setup_module(_module=None):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_seed_demo_creates_water_and_reaches():
    seed_demo(reset=True)
    with SessionLocal() as db:
        waters = db.query(models.WaterBody).all()
        reaches = db.query(models.Reach).all()
        assert len(waters) >= 1
        assert len(reaches) >= 1
