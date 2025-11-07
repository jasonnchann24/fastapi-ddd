from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi_ddd.core.logging import log_info

# --- Custom configurations here ---
INSTALLED_DOMAINS = ["authentication", "authorization"]

# --- ---- ---- ---- ---- ---- --- ---


BASE_DIR = Path(__file__).resolve().parents[3]
log_info(f"📁 (config.py) loads BASE_DIRECTORY: [bold blue]{BASE_DIR}[/bold blue]")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Installed domains ---
    installed_domains: list[str] = Field(default_factory=lambda: INSTALLED_DOMAINS)

    # --- JWT ---
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(3, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_cookie_domain: str = Field("", alias="JWT_COOKIE_DOMAIN")
    jwt_cookie_secure: bool = Field(False, alias="JWT_COOKIE_SECURE")
    jwt_cookie_samesite: str = Field("strict", alias="JWT_COOKIE_SAMESITE")

    # --- Database ---
    database_user: str = Field(..., alias="DATABASE_USER")
    database_password: str = Field(..., alias="DATABASE_PASSWORD")
    database_host: str = Field(..., alias="DATABASE_HOST")
    database_port: int = Field(..., alias="DATABASE_PORT")
    database_name: str = Field(..., alias="DATABASE_NAME")


settings = Settings()
