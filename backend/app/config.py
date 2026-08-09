from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_KEYS = {"", "dev-secret-change-me", "change-me", "changeme", "secret"}


class Settings(BaseSettings):
    # extra="ignore" matters more than it looks. Without it, any key in .env
    # that Settings does not declare is a hard startup failure -- and .env.example
    # ships SEED_USER_*, SEED_FORCE_RESET and BACKEND_PORT, which are read by
    # app/seed.py and docker-compose, not by this class. Copying the template
    # and running uvicorn crashed on all six. Docker never hit it, because
    # compose passes them as environment variables and those are ignored either
    # way; only the documented local-Python path broke.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field("HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    claim_lifetime_days: int = Field(30, alias="CLAIM_LIFETIME_DAYS")
    cors_origins: list[str] | str = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="CORS_ORIGINS",
    )

    @field_validator("secret_key")
    @classmethod
    def reject_placeholder_key(cls, value: str) -> str:
        # Every placeholder this repo has ever shipped is in the public git log,
        # so anyone can forge a token signed with one. Fail at startup rather
        # than serve traffic on a key a stranger can read.
        if value.strip().lower() in PLACEHOLDER_KEYS or len(value.strip()) < 32:
            raise ValueError(
                "SECRET_KEY is unset, too short, or a known placeholder. "
                'Generate one: python -c "import secrets; '
                'print(secrets.token_urlsafe(48))"'
            )
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()
