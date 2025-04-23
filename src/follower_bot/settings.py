from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Follower Bot: An automated bot for following GitHub users.
    """

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        cli_parse_args=True,
        cli_prog_name="follower-bot",
        cli_kebab_case=True,
    )

    APP_TITLE: str = Field(default="Follower Bot", description="Application title")
    GITHUB_TOKEN: str = Field(
        description="GitHub token for authentication",
    )
    BANNER_FILE: Optional[str] = Field(
        default="banner.txt", deprecated="Banner file path"
    )
    LOGURU_CONFIG_FILE: Optional[str] = Field(
        default="loguru.yaml",
        description="Loguru configuration file path",
    )
    JOB_INTERVAL: int = Field(
        default=4 * 60 * 60,
        ge=60 * 60,
        description="Interval between job runs in seconds (>= 3600)",
    )
    JOB_JITTER: int = Field(
        default=60 * 60,
        ge=0,
        description="Jitter for job interval in seconds (>= 0)",
    )
    JOB_FOLLOW_USER_BASE: int = Field(
        default=20,
        ge=1,
        description="Base number of users to follow per job run (>= 1)",
    )
    JOB_FOLLOW_USER_JITTER: int = Field(
        default=5,
        ge=0,
        description="Jitter for number of users to follow in job run (>= 0)",
    )
    JOB_RUN_NOW: bool = Field(
        default=True,
        description="Run job immediately",
    )
    FOLLOW_USER_MAX: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of users to follow (>= 1)",
    )
    SEARCH_USERS_PER_PAGE: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Number of users to fetch per page (1-100)",
    )
    SEARCH_QUERY: str = Field(
        description="Search query for GitHub API",
    )
    DATABASE_URL: str = Field(
        default="sqlite:///data/follower-bot.db",
        description="Database URL",
    )
    DATABASE_LOG_LEVEL: Optional[str] = Field(
        default=None,
        description="Database log level",
    )
