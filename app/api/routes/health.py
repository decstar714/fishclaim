from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db_ok = False
    status = "ok" if db_ok else "degraded"
    return {"status": status, "database": db_ok}
