from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages all application settings for the Global Integrity Service.
    It loads values from environment variables or a .env file.
    """
    # --- Upstash Redis Configuration ---
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str

    # --- API Security ---
    API_KEY: str

    # Pydantic settings configuration to load from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
