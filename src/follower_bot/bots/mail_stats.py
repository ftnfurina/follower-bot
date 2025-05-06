from datetime import datetime
from typing import Literal

from loguru import logger
from pydantic import Field
from sqlmodel import Session

from follower_bot.bots import (
    Bot,
    BotSettings,
    inject_history,
    inject_session,
    inject_state,
)
from follower_bot.email import Stats
from follower_bot.model import CreateBy, History, HistoryState, State


class MailStatsBotSettings(BotSettings):
    name: Literal["MailStatsBot"] = Field(
        default="MailStatsBot", description="Mutual follow bot"
    )


class MailStatsBot(Bot[MailStatsBotSettings]):
    name: str = "MailStatsBot"

    def join_scheduler(self):
        if self.email is None:
            logger.warning("Email settings not found, skipping mail stats bot")
            return

        return super().join_scheduler()

    @inject_session
    @inject_state
    @inject_history(CreateBy.MAIL_STATS)
    def exec(self, session: Session, state: State, history: History) -> None:
        start_date = state.stat_last_date
        end_date = datetime.now()

        stats = Stats(
            start_date=start_date,
            end_date=end_date,
            follower_count=self.store.query_follower_count(session),
            following_count=self.store.query_following_count(session),
        )

        histories = self.store.query_histories(
            start_date=start_date,
            end_date=end_date,
            session=session,
        )

        mappings = {
            CreateBy.FOLLOW_USER: "follow_user_count",
            CreateBy.MUTUAL_FOLLOW: "mutual_follow_count",
            CreateBy.MUTUAL_UNFOLLOW: "mutual_unfollow_count",
            CreateBy.UNFOLLOW_FOLLOWING: "unfollow_following_count",
        }

        for h in histories:
            field_name = mappings.get(h.create_by)
            if field_name is not None:
                setattr(stats, field_name, getattr(stats, field_name) + h.count)

        ok, error = self.email.send_stats(stats)

        if ok:
            history.count = 1
            state.stat_last_date = end_date
            logger.info("Sent stats email successfully")
        else:
            history.state = HistoryState.FAIL
            history.message = str(error)
