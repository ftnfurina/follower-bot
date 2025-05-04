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
from follower_bot.github import PER_PAGE_MAX, get_user_followers
from follower_bot.model import CreateBy, History, State, users2followers


class SyncFollowerBotSettings(BotSettings):
    name: Literal["SyncFollowerBot"] = Field(
        default="MutualUnfollowBot", description="Mutual unfollow bot"
    )


class SyncFollowerBot(Bot[SyncFollowerBotSettings]):
    name: str = "SyncFollowerBot"

    @inject_session
    @inject_state
    @inject_history(CreateBy.SYNC_FOLLOWER)
    def exec(self, session: Session, state: State, history: History) -> None:
        sync_id = self.generate_timestamp(default=state.sync_follower_id)
        logger.debug(f"Sync follower id: {sync_id}")
        state.sync_follower_id = sync_id

        while not self.stopped:
            logger.info(f"Sync follower page: {state.sync_follower_page}")
            users = get_user_followers(
                page=state.sync_follower_page,
                token=self.g_settings.github_token,
            )

            followers = users2followers(users, sync_id)
            self.store.upsert_followers(followers=followers, session=session)

            state.sync_follower_page += 1
            users_len = len(users)
            history.count += users_len

            if users_len < PER_PAGE_MAX:
                logger.info(f"Sync follower done, total {users_len} users")
                state.sync_follower_page = 1
                state.sync_follower_id = None
                break

        self.store.update_unfollow_followers(sync_id=sync_id, session=session)

        logger.info(f"Sync follower done, total {history.count} users")
