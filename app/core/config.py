from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/internships.db"
    openai_api_key: str = ""
    google_api_key: str = ""
    llm_provider: str = "auto"

    discovery_enabled: bool = False
    discovery_interval_hours: int = 6

    playwright_headless: bool = True
    application_automation_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
