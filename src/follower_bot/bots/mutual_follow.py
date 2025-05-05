from datetime import datetime
from typing import Literal

from loguru import logger
from pydantic import Field
from requests.exceptions import RequestException
from sqlmodel import Session

from follower_bot.bots import Bot, BotSettings, inject_history, inject_session
from follower_bot.github import put_user_following
from follower_bot.model import CreateBy, History, user2following


class MutualFollowBotSettings(BotSettings):
    name: Literal["MutualFollowBot"] = Field(
        default="MutualFollowBot", description="Mutual follow bot"
    )
    per_mutual_follow_count: int = Field(
        default=100, ge=1, description="Mutual follow count per run"
    )
    unfollow_threshold: int = Field(default=3, ge=1, description="Unfollow threshold")


class MutualFollowBot(Bot[MutualFollowBotSettings]):
    name: str = "MutualFollowBot"

    @inject_session
    @inject_history(CreateBy.MUTUAL_FOLLOW)
    def exec(self, session: Session, history: History) -> None:
        result = self.store.query_not_following_followers(
            limit=self.settings.per_mutual_follow_count,
            unfollow_threshold=self.settings.unfollow_threshold,
            session=session,
        )

        logger.info(f"Found {len(result)} not followed followers")

        for follower, following in result:
            if following is None:
                following = user2following(follower, CreateBy.MUTUAL_FOLLOW)

            try:
                following.create_by = CreateBy.MUTUAL_FOLLOW
                put_user_following(follower.login, self.g_settings.github_token)
                following.last_follow_date = datetime.now()
                following.followed = True

                logger.info(f"Followed: {follower}")
                history.count += 1
            except RequestException as e:
                logger.error(f"Failed to follow: {follower.login}, {e}")
                if e.response is None or e.response.status_code in [401, 403, 422]:
                    raise e
                continue
            finally:
                self.store.upsert_following(following=following, session=session)

        logger.info(f"Followed {history.count} users")
