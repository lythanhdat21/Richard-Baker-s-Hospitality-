from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    internal_api_key: str = "change-me-in-production"

    database_url: str = "postgresql://opera_user:opera_pass@localhost:5432/opera_bridge"

    opera_client_id: str = ""
    opera_client_secret: str = ""
    opera_base_url: str = ""
    opera_hotel_id: str = ""
    opera_token_ttl: int = 3300


settings = Settings()
