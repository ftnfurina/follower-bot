import sys
from typing import Optional

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """
    Settings for the database.
    """

    url: str = Field(default="sqlite:///data/store.db", description="Database URL")
    log_level: Optional[str] = Field(
        default=None, description="Log level for the database"
    )


class Settings(BaseSettings):
    """
    Follower Bot: An automated bot for following and reciprocating follows with GitHub users.
    """

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        cli_parse_args=True,
        cli_prog_name="follower-bot",
        env_nested_delimiter=".",
        cli_kebab_case=True,
        extra="ignore",
    )

    github_token: str = Field(description="GitHub token for authentication")
    banner_file: Optional[str] = Field(
        default="banner.txt",
        description="Path to the banner file to display on the console",
    )
    loguru_config_file: Optional[str] = Field(
        default="loguru.yaml", description="Path to the loguru configuration file"
    )
    bots_file: Optional[str] = Field(
        default="bots.yaml", description="Path to the bots configuration file"
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings, description="Settings for the database"
    )


def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)
