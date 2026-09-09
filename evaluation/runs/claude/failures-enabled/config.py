"""Application settings.

Every knob that governs failure behaviour (timeouts, retry counts, pool
bounds, reconciliation cadence) lives here so it is explicit and tunable
rather than hidden in call sites.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Database ---------------------------------------------------------
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/courses"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_timeout: float = 10.0

    # --- Paystack ---------------------------------------------------------
    paystack_secret_key: str = "sk_test_changeme"
    paystack_public_key: str = "pk_test_changeme"
    paystack_base_url: str = "https://api.paystack.co"
    # A bounded timeout on every call: a hanging dependency must never pin a
    # worker indefinitely. The read timeout expiring means "unknown", not
    # "failed" - see adapter/paystack.py.
    paystack_timeout_seconds: float = 10.0
    # Retries are only safe because we send a stable `reference` /
    # Idempotency-Key, making the calls idempotent on Paystack's side.
    paystack_max_retries: int = 2

    # --- Reconciliation ---------------------------------------------------
    reconcile_min_age_seconds: int = 120
    reconcile_interval_seconds: int = 300
    reconcile_batch_size: int = 100
    reconcile_abandon_after_seconds: int = 3600

    # --- App --------------------------------------------------------------
    public_base_url: str = "http://localhost:8000"
    run_reconcile_in_process: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
