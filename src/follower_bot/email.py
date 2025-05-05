from datetime import datetime
from email.mime.text import MIMEText
from smtplib import SMTP
from typing import Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field
from rate_keeper import RateKeeper

from .file import read_file
from .settings import EmailSettings

rate_keeper = RateKeeper(limit=4, period=60)


class Stats(BaseModel):
    start_date: datetime = Field(default=datetime.now, description="Start date")
    end_date: datetime = Field(default_factory=datetime.now, description="End date")
    follower_count: int = Field(default=0, description="Number of followers")
    following_count: int = Field(default=0, description="Number of following")
    follow_user_count: int = Field(default=0, description="Number of users followed")
    mutual_follow_count: int = Field(default=0, description="Number of mutual follow")
    mutual_unfollow_count: int = Field(
        default=0, description="Number of mutual unfollow"
    )
    unfollow_following_count: int = Field(
        default=0, description="Number of unfollowed following"
    )


class BotError(BaseModel):
    name: str = Field(default="Follower Bot", description="Name of the bot")
    message: str = Field(description="Error message")
    traceback: str = Field(description="Traceback")


EmailResult = Tuple[bool, Optional[Exception]]


class Email:
    def __init__(self, settings: EmailSettings):
        self.settings = settings

    @rate_keeper.decorator
    def send_email(
        self, subject: str, message: str, email_type: str = "plain"
    ) -> EmailResult:
        try:
            msg = MIMEText(message, email_type)
            msg["Subject"] = subject
            msg["From"] = (
                f"{self.settings.smtp_sender_name} <{self.settings.sender_email}>"
            )
            msg["To"] = ", ".join(self.settings.recipient_emails)

            with SMTP(self.settings.smtp_server, self.settings.smtp_port) as server:
                server.starttls()
                server.login(
                    user=self.settings.smtp_username,
                    password=self.settings.smtp_password,
                )
                server.sendmail(
                    from_addr=self.settings.sender_email,
                    to_addrs=self.settings.recipient_emails,
                    msg=msg.as_string(),
                )
            return True, None
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False, e

    def send_stats(self, stats: Stats) -> EmailResult:
        template = read_file(self.settings.stats_template_file)
        return self.send_email(
            subject="Follower Bot Stats",
            message=template.format(stats=stats),
            email_type="html",
        )

    def send_error(self, error: BotError) -> EmailResult:
        template = read_file(self.settings.error_template_file)
        return self.send_email(
            subject="Follower Bot Error",
            message=template.format(error=error),
            email_type="html",
        )
