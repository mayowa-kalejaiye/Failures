"""Application configuration loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database (async SQLAlchemy URL)
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/course_payments"
    )

    # Paystack
    PAYSTACK_SECRET_KEY: str = "sk_test_changeme"
    PAYSTACK_PUBLIC_KEY: str = "pk_test_changeme"
    PAYSTACK_BASE_URL: str = "https://api.paystack.co"
    PAYSTACK_CALLBACK_URL: str = "http://localhost:8000/payments/callback"

    # Auth / JWT
    JWT_SECRET_KEY: str = "change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # App
    DEFAULT_CURRENCY: str = "NGN"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
