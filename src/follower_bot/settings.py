import sys
from typing import Optional, Literal

from pydantic import Field, ValidationError, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class TriggerSettings(BaseModel):
    """
    Settings for the trigger.
    """

    name: Literal["interval", "cron"] = Field(
        default="interval",
        description="Type of the trigger",
    )
    weeks: int = Field(default=0, ge=0, description="[interval] Weeks")
    days: int = Field(default=0, ge=0, description="[interval] Days")
    hours: int = Field(default=0, ge=0, description="[interval] Hours")
    minutes: int = Field(default=0, ge=0, description="[interval] Minutes")
    seconds: int = Field(default=0, ge=0, description="[interval] Seconds")
    jitter: Optional[int] = Field(
        default=None,
        ge=0,
        description="[interval] Jitter for the interval trigger",
    )
    expr: str = Field(
        default="* * * * *",
        description="[cron] Cron expression for the trigger",
    )
    timezone: Optional[str] = Field(
        default=None,
        description="[interval,cron] Timezone for the trigger",
    )


class FollowingBotSettings(BaseModel):
    """
    Settings for the following bot.
    """

    enabled: bool = Field(
        default=False,
        description="Enable the following bot",
    )
    trigger: TriggerSettings = Field(
        default_factory=TriggerSettings, description="Settings for the trigger"
    )
    mode: Literal["all", "follow_new", "follow_back"] = Field(
        default="all",
        description="Mode for the following bot",
    )
    run_now: bool = Field(
        default=True,
        description="Run the trigger immediately",
    )
    follow_max: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of follows",
    )
    per_follow_base: int = Field(
        default=20,
        ge=1,
        description="The basic number of follows to do per run",
    )
    per_follow_jitter: int = Field(
        default=5,
        ge=0,
        description="The jitter for the number of follows to do per run",
    )


class FollowerBotSettings(BaseModel):
    """
    Settings for the follower bot.
    """

    enabled: bool = Field(
        default=False,
        description="Enable the follower bot",
    )
    trigger: TriggerSettings = Field(
        default_factory=TriggerSettings, description="Settings for the trigger"
    )
    run_now: bool = Field(
        default=True,
        description="Run the trigger immediately",
    )
    follow_back: bool = Field(
        default=True,
        description="Follow back the followers",
    )
    unfollow_unfollowed: bool = Field(
        default=True,
        description="Unfollow unfollowed users",
    )


class DatabaseSettings(BaseModel):
    """
    Settings for the database.
    """

    url: str = Field(
        default="sqlite:///data/store.db",
        description="Database URL",
    )
    log_level: Optional[str] = Field(
        default=None,
        description="Log level for the database",
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

    github_token: str = Field(
        description="GitHub token for authentication",
    )
    banner_file: Optional[str] = Field(
        default="banner.txt",
        description="Path to the banner file to display on the console",
    )
    loguru_config_file: Optional[str] = Field(
        default="loguru.yaml",
        description="Path to the loguru configuration file",
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Settings for the database",
    )
    following_bot: FollowingBotSettings = Field(
        default_factory=FollowingBotSettings,
        description="Settings for the following bot",
    )
    follower_bot: FollowerBotSettings = Field(
        default_factory=FollowerBotSettings,
        description="Settings for the follower bot",
    )


def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)


def create_trigger(trigger_settings: TriggerSettings) -> BaseTrigger:
    if trigger_settings.name == "cron":
        return CronTrigger.from_crontab(
            expr=trigger_settings.expr,
            timezone=trigger_settings.timezone,
        )
    elif trigger_settings.name == "interval":
        return IntervalTrigger(
            weeks=trigger_settings.weeks,
            days=trigger_settings.days,
            hours=trigger_settings.hours,
            minutes=trigger_settings.minutes,
            seconds=trigger_settings.seconds,
            jitter=trigger_settings.jitter,
            timezone=trigger_settings.timezone,
        )
