from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages all application settings for the Global Integrity Service.
    It loads values from environment variables or a .env file.
    """
    # --- Redis Configuration ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # --- API Security ---
    # This key is used to protect the /validate-global-uniqueness endpoint.
    # It must be provided in the 'X-API-KEY' header of incoming requests.
    API_KEY: str

    # Pydantic settings configuration to load from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Create a single, reusable instance of the settings
settings = Settings()
