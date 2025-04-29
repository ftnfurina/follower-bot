from datetime import datetime

from apscheduler.util import undefined
from loguru import logger
from requests import RequestException

from ..github import PER_PAGE_MAX, delete_user_following, get_user_followers
from ..model import (
    FollowingCreateBy,
    History,
    HistoryType,
    State,
    users2followers,
    users2followings,
)
from ..settings import create_trigger
from .bot import Bot, inject_history


class FollowerBot(Bot):
    def join_scheduler(self):
        if not self.settings.follower_bot.enabled:
            logger.info("Follower Bot is disabled")
            return

        self.scheduler.add_job(
            self.exec,
            trigger=create_trigger(self.settings.follower_bot.trigger),
            id="follower-bot",
            misfire_grace_time=60,
            next_run_time=datetime.now()
            if self.settings.follower_bot.run_now
            else undefined,
        )

    def _unfollow_followers(self, search_id: int):
        unfollow_followers = self.store.query_unfollow_followers(search_id)
        logger.info(f"Find {len(unfollow_followers)} unfollow followers")

        for i, follower in enumerate(unfollow_followers):
            if self.is_stopped():
                break

            try:
                delete_user_following(follower.login, self.settings.github_token)
                logger.info(f"Unfollowed {follower.login}")
                follower.follower = False
                follower.unfollow_count += 1
                self.store.update_follower(follower)
                self.store.delete_following(follower.id)
            except RequestException as e:
                logger.warning(f"Failed to unfollow: {follower.login}")
                if e.response is None or e.response.status_code in [401, 403, 422]:
                    raise e
                continue

    def _query_followers(self, search_id: int, history: History, state: State):
        while True:
            if self.is_stopped():
                break

            users = get_user_followers(
                page=state.follower_last_page,
                token=self.settings.github_token,
            )

            self.store.upsert_followers(users2followers(users, search_id))

            if self.settings.follower_bot.follow_back:
                self.store.add_followings(
                    users2followings(users, FollowingCreateBy.FOLLOWER_BOT)
                )

            state.follower_last_page += 1
            history.count += len(users)

            if len(users) < PER_PAGE_MAX:
                state.follower_last_page = 1
                logger.info("Search followers has finished")
                break

    @logger.catch(reraise=False)
    @inject_history(HistoryType.FOLLOWER)
    def exec(self, history: History):
        logger.info("Running follower bot")
        state = self.store.query_state()

        search_id = (
            state.follower_search_id
            if state.follower_last_page != 1
            else int(datetime.now().timestamp())
        )

        self._query_followers(search_id, history, state)

        state.follower_search_id = search_id
        self.store.update_state(state)

        if self.settings.follower_bot.unfollow_unfollowed:
            self._unfollow_followers(search_id)

        logger.info("Follower Bot has finished")
