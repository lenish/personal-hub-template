"""Application configuration using environment variables."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Core Settings
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Environment
    environment: str = "production"
    log_level: str = "INFO"

    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://hub_user:password@localhost:5432/personal_hub"

    # Redis (optional, for caching)
    redis_url: str = "redis://localhost:6379/0"

    # API Authentication
    api_key: str = ""  # If empty, auth is disabled (dev mode)

    # CORS
    cors_origins: str = "http://localhost:3000"  # Comma-separated list

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Feature Flags - Enable/Disable Data Sources
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    enable_whoop: bool = False
    enable_apple_health: bool = False
    enable_withings: bool = False
    enable_slack: bool = False
    enable_telegram: bool = False
    enable_google_calendar: bool = False
    enable_spotify: bool = False
    enable_notion: bool = False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Health Data Sources
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Whoop
    whoop_client_id: str = ""
    whoop_client_secret: str = ""
    whoop_redirect_uri: str = "http://localhost:8000/api/health/whoop/callback"
    whoop_sync_interval: int = 5  # minutes

    # Apple Health (webhook from iOS app)
    apple_health_webhook_token: str = ""

    # Withings
    withings_client_id: str = ""
    withings_client_secret: str = ""
    withings_redirect_uri: str = "http://localhost:8000/api/health/withings/callback"
    withings_sync_interval: int = 5  # minutes

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Communication Data Sources
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Slack
    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_channel_filter: str = ""  # Comma-separated channel IDs
    slack_sync_interval: int = 10  # minutes

    # Telegram
    telegram_bot_token: str = ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Productivity Data Sources
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Google (OAuth for Calendar, Gmail, etc.)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_calendar_ids: str = "primary"  # Comma-separated calendar IDs
    google_geocoding_api_key: str = ""  # For location enrichment

    # Notion
    notion_api_key: str = ""
    notion_database_ids: str = ""  # Comma-separated database IDs

    # Spotify
    spotify_client_id: str = ""
    spotify_client_secret: str = ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI & Analysis
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Claude CLI (for AI analysis)
    claude_cli_path: str = "claude"  # Path to claude binary

    # OpenAI (alternative)
    openai_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


# Global settings instance
settings = Settings()
