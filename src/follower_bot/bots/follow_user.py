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
from follower_bot.github import PER_PAGE_MAX, get_user, get_users, put_user_following
from follower_bot.model import CreateBy, GithubUser, History, State, user2following


class FollowUserBotSettings(BotSettings):
    name: Literal["FollowUserBot"] = Field(
        default="FollowUserBot", description="Follow user bot"
    )
    search_page_max: int = Field(
        default=10,
        ge=1,
        description=f"Maximum number of search pages (page size is {PER_PAGE_MAX})",
    )
    per_follow_max: int = Field(
        default=30, description="Maximum number of users to follow per run"
    )
    filter_expr: Optional[str] = Field(
        default=None, description="Filter expression for users to follow"
    )

    @field_validator("filter_expr")
    def validate_filter_expr(cls, v) -> Optional[str]:
        if v is None:
            return v
        v_strip = v.strip()
        if v_strip != "":
            validate(scan(v))
        return v if v_strip != "" else None


class FollowUserBot(Bot[FollowUserBotSettings]):
    name: str = "FollowUserBot"

    def __init__(self, *args, **kwargs):
        super(FollowUserBot, self).__init__(*args, **kwargs)

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
    @inject_history(CreateBy.FOLLOW_USER)
    def exec(self, session: Session, state: State, history: History) -> None:
        for _ in range(self.settings.per_follow_max):
            if self.stopped:
                break

            users = get_users(
                since=state.follow_user_since,
                token=self.g_settings.github_token,
            )

            for user in users:
                if self.stopped:
                    break

                try:
                    github_user = get_user(
                        user_login=user.login,
                        token=self.g_settings.github_token,
                    )

                    if not self.check_github_user(github_user):
                        logger.info(f"Filtered: {github_user}")
                        continue

                    following = user2following(user, CreateBy.FOLLOW_USER)

                    put_user_following(following.login, self.g_settings.github_token)
                    following.followed = True
                    self.store.upsert_following(following=following, session=session)

                    logger.info(f"Followed: {github_user}")
                    state.follow_user_since = user.id

                    history.count += 1
                except RequestException as e:
                    logger.error(f"Failed to follow: {following.login}, {e}")
                    if e.response is None or e.response.status_code in [401, 403, 422]:
                        raise e
                    continue

                if history.count >= self.settings.per_follow_max:
                    break

            if len(users) < PER_PAGE_MAX:
                logger.info("No more users to follow, stopping bot")
                self.stop()

            if history.count >= self.settings.per_follow_max:
                break

        logger.info(f"Followed {history.count} users")
