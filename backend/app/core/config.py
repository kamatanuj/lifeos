"""LifeOS Backend Configuration"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LifeOS API"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:a2781edc12d3bbc67320c1c4a0c7f18bca793cad9c109ea32e801493d646af63@127.0.0.1:5432/lifeos"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "lifeos-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()