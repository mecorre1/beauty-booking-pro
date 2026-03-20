from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"
    jwt_secret: str = "dev-insecure-change-me-use-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    # Display surcharge for at-home (EUR); US-012 may keep this as non-DB constant.
    at_home_display_surcharge_eur: float = 12.5
    # Optional: create first admin on startup when DB has no users. Defaults are for local dev only;
    # override or set empty to disable (BOOTSTRAP_ADMIN_EMAIL=).
    bootstrap_admin_email: str | None = "admin@admin.com"
    bootstrap_admin_password: str | None = "admin"
    # Used in booking confirmation emails for edit/cancel links.
    public_app_base_url: str = "http://127.0.0.1:5173"


settings = Settings()
