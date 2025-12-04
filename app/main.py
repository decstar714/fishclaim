from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from . import models
from .routes import health, waters, catches, claims, auth, sessions, species, mapdata

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FishClaim API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(waters.router, prefix="/api")
app.include_router(catches.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(species.router, prefix="/api")
app.include_router(mapdata.router, prefix="/api")
