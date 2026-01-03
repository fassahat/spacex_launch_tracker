"""Application configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    spacex_api_base_url: str = "https://api.spacexdata.com/v4"
    api_timeout: int = 30

    # Cache Configuration
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_enabled: bool = True

    # Application Configuration
    app_name: str = "SpaceX Launch Tracker"
    app_version: str = "1.0.0"
    debug: bool = False

    class Config:
        """Pydantic settings config."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
