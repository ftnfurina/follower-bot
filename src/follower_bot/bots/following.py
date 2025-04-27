import random
from datetime import datetime
from typing import List, Tuple

from apscheduler.util import undefined
from loguru import logger
from requests import RequestException

from ..github import PER_PAGE_MAX, get_search_users, put_user_following
from ..model import Following, FollowingCreateBy, History, HistoryType, users2followings
from ..settings import create_trigger
from .bot import Bot, inject_history


class FollowingBot(Bot):
    def join_scheduler(self):
        if not self.settings.following_bot.enabled:
            logger.info("Following Bot is disabled")
            return

        self.scheduler.add_job(
            self.exec,
            trigger=create_trigger(self.settings.following_bot.trigger),
            id="following-bot",
            next_run_time=datetime.now()
            if self.settings.following_bot.run_now
            else undefined,
        )

    def _is_limit_reached(self) -> bool:
        if self.settings.following_bot.follow_max is None:
            return False

        following_count = self.store.query_following_count()
        return following_count >= self.settings.following_bot.follow_max

    def _get_follow_count(self) -> int:
        return self.settings.following_bot.per_follow_base + random.randint(
            0,
            self.settings.following_bot.per_follow_jitter,
        )

    def _get_unfollowed_following(self, count: int) -> Tuple[bool, List[Following]]:
        followings = self.store.query_unfollowed_following(count)
        state = self.store.query_state()

        while len(followings) < count:
            if self.is_stopped():
                return False, followings

            logger.debug(
                f"Not enough unfollowed followings: {len(followings)}. Start fetch more users"
            )
            logger.debug(f"Last page: {state.following_last_since}")

            users = get_search_users(
                since=state.following_last_since,
                token=self.settings.github_token,
            )

            self.store.add_followings(
                users2followings(users, FollowingCreateBy.FOLLOWING_BOT)
            )

            logger.success(f"Fetched {len(users)} users")

            followings = self.store.query_unfollowed_following(count)

            if len(users) < PER_PAGE_MAX:
                return True, followings

            state.following_last_since = users[-1].id
            self.store.update_state(state)
            self.sleep()

        return False, followings

    def _follow_followings(self, followings: List[Following], history: History) -> None:
        for i, following in enumerate(followings):
            if self.is_stopped():
                return

            logger.info(
                f"Start following: {i + 1}/{len(followings)}: {following.login}"
            )

            try:
                put_user_following(
                    user_login=following.login,
                    token=self.settings.github_token,
                )
                logger.success(f"Followed: {following.login}")
                history.count += 1
                following.followed = True
                following.followed_date = datetime.now()
            except RequestException as e:
                logger.warning(f"Failed to follow: {following.login}")
                if e.response is None or e.response.status_code in [401, 403, 422]:
                    following.fail_count += 1
                    raise e
                self.sleep(4, 6)
                continue
            finally:
                self.store.update_following(following)

            self.sleep()

    @logger.catch(reraise=False)
    @inject_history(HistoryType.FOLLOWING)
    def exec(self, history: History):
        logger.info("Running following bot")

        if self._is_limit_reached():
            logger.info(
                f"Following limit reached: {self.settings.following_bot.follow_max}"
            )
            self.shutdown()
            return

        follow_count = self._get_follow_count()
        logger.debug(f"Following count: {follow_count}")

        is_over, followings = self._get_unfollowed_following(follow_count)
        logger.debug(f"Is over: {is_over}")

        self._follow_followings(followings, history)

        if is_over:
            logger.info("Following bot is over")
            self.shutdown()
            return

        logger.info("Following Bot has finished")
