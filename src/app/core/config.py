import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Capture any extra keys from .env
    )

    DATABASE_URL: str = Field(
        default_factory=lambda: f"postgresql+asyncpg://{os.getenv('USER', 'postgres')}@localhost:5432/pine-blogs",
    )
    SQL_ECHO: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - comma-separated origins, or "*" for all
    CORS_ORIGINS: str = "*"


settings = Settings()
