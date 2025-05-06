import os
import sys
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """
    Settings for the database.
    """

    url: str = Field(default="sqlite:///data/store.db", description="Database URL")
    log_level: Optional[str] = Field(
        default=None, description="Log level for the database"
    )


class EmailSettings(BaseModel):
    """
    Settings for the email.
    """

    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_sender_name: str = Field(
        default="Follower Bot", description="SMTP sender name"
    )
    smtp_username: str = Field(description="SMTP username")
    smtp_password: str = Field(description="SMTP password")
    sender_email: str = Field(description="Sender email address")
    recipient_emails: List[str] = Field(
        min_length=1, description="List of recipient email addresses"
    )
    stats_template_file: Optional[str] = Field(
        default="email/stats_template.html",
        description="Path to the HTML template for the email stats",
    )
    error_template_file: Optional[str] = Field(
        default="email/error_template.html",
        description="Path to the HTML template for the email error",
    )

    @field_validator("stats_template_file")
    def validate_stats_template_file(cls, v):
        if not os.path.isfile(v):
            raise ValueError(f"Stats template file {v} does not exist")
        return v

    @field_validator("error_template_file")
    def validate_error_template_file(cls, v):
        if not os.path.isfile(v):
            raise ValueError(f"Error template file {v} does not exist")
        return v


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
    enabled_error_email: bool = Field(
        default=True, description="Enable sending error email"
    )
    email: Optional[EmailSettings] = Field(
        default=None, description="Settings for the email"
    )


def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)
