from typing import Literal

from loguru import logger
from pydantic import Field
from requests.exceptions import RequestException
from sqlmodel import Session

from follower_bot.bots import Bot, BotSettings, inject_history, inject_session
from follower_bot.github import delete_user_following
from follower_bot.model import CreateBy, History


class MutualUnfollowBotSettings(BotSettings):
    name: Literal["MutualUnfollowBot"] = Field(
        default="MutualUnfollowBot", description="Mutual unfollow bot"
    )
    per_mutual_unfollow_count: int = Field(
        default=100, ge=1, description="Mutual unfollow count per run"
    )
    not_create_by_user: bool = Field(
        default=True, description="Whether to exclude following created by the user"
    )


class MutualUnfollowBot(Bot[MutualUnfollowBotSettings]):
    name: str = "MutualUnfollowBot"

    @inject_session
    @inject_history(CreateBy.MUTUAL_UNFOLLOW)
    def exec(self, session: Session, history: History) -> None:
        result = self.store.query_unfollow_followers(
            limit=self.settings.per_mutual_unfollow_count,
            not_create_by_user=self.settings.not_create_by_user,
            session=session,
        )
        logger.info(f"Found {len(result)} unfollow followers")

        for follower, following in result:
            try:
                delete_user_following(follower.login, self.g_settings.github_token)
                following.followed = False
                following.unfollow_count += 1
                logger.info(f"Unfollow: {follower}")
                history.count += 1
            except RequestException as e:
                logger.error(f"Failed to unfollow: {follower.login}, {e}")
                if e.response is None or e.response.status_code in [401, 403, 422]:
                    raise e
                continue
            finally:
                self.store.upsert(model=following, session=session)

        logger.info(f"Unfollowed {history.count} users")
