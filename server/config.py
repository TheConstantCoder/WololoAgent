"""Application configuration and settings.

Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini
    gemini_api_key: str = ""
    # Flagship Live model for bidirectional voice
    gemini_model: str = "models/gemini-2.5-flash-native-audio-latest"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Data
    game_data_path: str = "data/game_data.json"

    model_config = {"env_prefix": "WOLOLO_", "env_file": ".env"}


settings = Settings()
