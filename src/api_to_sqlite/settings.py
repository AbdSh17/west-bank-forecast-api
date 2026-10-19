"""Typed settings read from environment variables and the .env file."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """The MySQL settings. Names match the .env variables in any letter case."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = Field(min_length=1)
    mysql_password: SecretStr
    mysql_database: str = "weather"
    mysql_pool_size: int = Field(default=5, ge=1, le=32)
    mysql_test_database: str = "weather_test"


@lru_cache
def get_settings() -> Settings:
    """Return the settings, read once and then cached."""
    return Settings()
