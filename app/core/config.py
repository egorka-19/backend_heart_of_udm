from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Technostrelka API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/technostrelka"

    secret_key: str = "change-me-in-production-use-long-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    upload_dir: str = "./uploads"
    public_base_url: str = "http://10.0.2.2:8000"  # Android emulator -> host

    # Optional: OpenAI-compatible chat (set in .env for production)
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    feature_flag_metrics: bool = True


settings = Settings()
