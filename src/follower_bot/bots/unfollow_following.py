from typing import Literal, Optional

from loguru import logger
from pydantic import Field, field_validator
from requests.exceptions import RequestException
from sqlmodel import Session

from follower_bot.bots import (
    Bot,
    BotSettings,
    inject_history,
    inject_session,
    inject_state,
)
from follower_bot.evaluator import evaluate, infix_to_postfix, scan, validate
from follower_bot.github import PER_PAGE_MAX, delete_user_following, get_user
from follower_bot.model import CreateBy, GithubUser, History, State


class UnfollowFollowingBotSettings(BotSettings):
    name: Literal["UnfollowFollowingBot"] = Field(
        default="UnfollowFollowingBot", description="Unfollow Following Bot"
    )
    page_max: int = Field(
        default=10,
        ge=1,
        description=f"Maximum number of pages (page size is {PER_PAGE_MAX})",
    )
    per_unfollow_max: int = Field(
        default=30, description="Maximum number of users to unfollow per run"
    )
    filter_expr: Optional[str] = Field(
        default=None, description="Filter expression for users to unfollow"
    )

    @field_validator("filter_expr")
    def validate_filter_expr(cls, v) -> Optional[str]:
        if v is None:
            return v
        v_strip = v.strip()
        if v_strip != "":
            validate(scan(v))
        return v if v_strip != "" else None


class UnfollowFollowingBot(Bot[UnfollowFollowingBotSettings]):
    name: str = "UnfollowFollowingBot"

    def __init__(self, *args, **kwargs):
        super(UnfollowFollowingBot, self).__init__(*args, **kwargs)

        self.postfix_tokens = None
        if self.settings.filter_expr is not None:
            tokens = scan(self.settings.filter_expr)
            self.postfix_tokens = infix_to_postfix(tokens)

    def check_github_user(self, user: GithubUser) -> bool:
        if self.settings.filter_expr is None:
            return True
        return evaluate(self.postfix_tokens, user)

    @inject_session
    @inject_state
    @inject_history(CreateBy.UNFOLLOW_FOLLOWING)
    def exec(self, session: Session, state: State, history: History) -> None:
        for _ in range(self.settings.page_max):
            if self.stopped:
                break

            followings = self.store.query_followed_followings(
                since=state.unfollow_following_since,
                limit=PER_PAGE_MAX,
                session=session,
            )

            followings_len = len(followings)
            logger.info(f"Unfollow {followings_len} followings")

            for following in followings:
                if self.stopped:
                    break

                try:
                    if self.settings.filter_expr is not None:
                        github_user = get_user(
                            user_login=following.login,
                            token=self.g_settings.github_token,
                        )
                        if not self.check_github_user(github_user):
                            logger.info(f"Skip following: {following}")
                            continue

                    delete_user_following(following.login, self.g_settings.github_token)
                    following.followed = False
                    following.unfollow_count += 1

                    logger.info(f"Unfollowed: {following}")
                    state.unfollow_following_since = following.id

                    history.count += 1
                except RequestException as e:
                    logger.error(f"Failed to unfollow: {following.login}, {e}")
                    if e.response is None or e.response.status_code in [401, 403, 422]:
                        raise e
                    continue
                finally:
                    self.store.upsert_following(following=following, session=session)

                if history.count >= self.settings.per_unfollow_max:
                    break

            if followings_len < PER_PAGE_MAX:
                state.unfollow_following_since = 0
                break

            if history.count >= self.settings.per_unfollow_max:
                break

        logger.info(f"Unfollow {history.count} users")
