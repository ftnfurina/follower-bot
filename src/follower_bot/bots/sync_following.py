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
from follower_bot.github import PER_PAGE_MAX, get_user_following
from follower_bot.model import CreateBy, History, State, users2followings


class SyncFollowingBotSettings(BotSettings):
    name: Literal["SyncFollowingBot"] = Field(
        default="SyncFollowingBot", description="Sync following bot"
    )


class SyncFollowingBot(Bot[SyncFollowingBotSettings]):
    name: str = "SyncFollowingBot"

    @inject_session
    @inject_state
    @inject_history(CreateBy.SYNC_FOLLOWING)
    def exec(self, session: Session, state: State, history: History) -> None:
        sync_id = self.generate_timestamp(default=state.sync_following_id)
        state.sync_following_id = sync_id

        while not self.stopped:
            users = get_user_following(
                page=state.sync_following_page,
                token=self.g_settings.github_token,
            )

            followings = users2followings(users, CreateBy.USER, sync_id)
            self.store.upsert_followings(followings=followings, session=session)

            state.sync_following_page += 1
            users_len = len(users)
            history.count += users_len

            if users_len < PER_PAGE_MAX:
                logger.info(f"Sync following done, total {users_len} users")
                state.sync_following_page = 1
                state.sync_following_id = None
                break

        self.store.update_unfollow_followings(sync_id=sync_id, session=session)

        logger.info(f"Sync following done, total {history.count} users")
