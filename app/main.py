import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, catches, claims, health, reaches, waters, map, stats
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title="FishClaim API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Callable):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.on_event("startup")
    def on_startup():
        init_db()

    app.include_router(health.router, prefix="/api")
    app.include_router(waters.router, prefix="/api")
    app.include_router(reaches.router, prefix="/api")
    app.include_router(catches.router, prefix="/api")
    app.include_router(claims.router, prefix="/api")
    app.include_router(map.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    return app


app = create_app()
