"""
Application configuration.

All settings are read from environment variables (or a `.env` file) so that
secrets never live in source control. See `backend/.env.example`.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AIMode = Literal["mock", "local", "gemini", "groq", "hybrid"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App -----------------------------------------------------------------
    app_name: str = "Dark Shield API"
    app_env: str = Field(default="development", alias="APP_ENV")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Database ------------------------------------------------------------
    mongodb_uri: str = Field(default="", alias="MONGODB_URI")
    mongodb_database: str = Field(default="dark_shield", alias="MONGODB_DATABASE")

    # --- Cache ---------------------------------------------------------------
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")

    # --- Auth (Clerk) --------------------------------------------------------
    clerk_secret_key: str = Field(default="", alias="CLERK_SECRET_KEY")
    clerk_jwks_url: str = Field(default="", alias="CLERK_JWKS_URL")
    clerk_issuer: str = Field(default="", alias="CLERK_ISSUER")
    # When true (development only), requests without a valid Clerk token are
    # attributed to a demo user so the whole product can be explored locally.
    auth_dev_bypass: bool = Field(default=True, alias="AUTH_DEV_BYPASS")

    # --- AI ------------------------------------------------------------------
    ai_mode: AIMode = Field(default="mock", alias="AI_MODE")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")

    # --- Scraping ------------------------------------------------------------
    scraper_mode: Literal["mock", "playwright", "httpx"] = Field(default="mock", alias="SCRAPER_MODE")
    scraper_timeout_ms: int = Field(default=20000, alias="SCRAPER_TIMEOUT_MS")
    allow_private_urls: bool = Field(default=False, alias="ALLOW_PRIVATE_URLS")

    # --- Security ------------------------------------------------------------
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    max_request_bytes: int = Field(default=64 * 1024, alias="MAX_REQUEST_BYTES")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
