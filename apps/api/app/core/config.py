from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://opsmind:opsmind@localhost:5432/opsmind")
    jwks_url: str = os.getenv("JWKS_URL", "")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "")
    dev_auth_bypass: bool = os.getenv("DEV_AUTH_BYPASS", "false").lower() == "true"
    cors_allow_origins: list[str] = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))


@lru_cache

def get_settings() -> Settings:
    return Settings()
