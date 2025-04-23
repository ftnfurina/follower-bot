import random
import signal
import time
from datetime import datetime
from typing import List, Tuple

from apscheduler.events import EVENT_SCHEDULER_SHUTDOWN
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import undefined
from loguru import logger
from requests.exceptions import RequestException

from .banner import print_banner
from .github import fetch_follow_user, fetch_users
from .log import init_logging
from .model import User
from .settings import Settings
from .store import Store

settings = Settings()
scheduler = BackgroundScheduler()
init_logging(settings.LOGURU_CONFIG_FILE)
print_banner(settings.BANNER_FILE)
store = Store(settings.DATABASE_URL, settings.DATABASE_LOG_LEVEL)


def signal_handler(_signal, _frame):
    logger.info("Received signal, shutting down scheduler...")
    scheduler.shutdown(wait=False)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

scheduler.add_listener(lambda _: store.close(), EVENT_SCHEDULER_SHUTDOWN)


def get_unfollowed_users(follow_count: int) -> Tuple[List[User], bool]:
    users = store.query_unfollowed_users(follow_count)
    last_page = store.last_page

    while len(users) < follow_count:
        logger.info("Not enough unfollowed users, starting to fetch more users...")
        logger.debug(f"Last page: {last_page}")
        last_page = last_page + 1
        search_users = fetch_users(
            page=last_page,
            per_page=settings.SEARCH_USERS_PER_PAGE,
            q=settings.SEARCH_QUERY,
            token=settings.GITHUB_TOKEN,
        )
        add_count = store.add_users(search_users)
        logger.success(f"Added {add_count} users to database")
        store.update_last_page(last_page)
        users = store.query_unfollowed_users(follow_count)
        time.sleep(random.randint(2, 4))

        if len(search_users) < settings.SEARCH_USERS_PER_PAGE:
            return users, True

    return users, False


def is_follow_limit_reached() -> bool:
    if settings.FOLLOW_USER_MAX is None:
        return False
    return store.followed_users_count >= settings.FOLLOW_USER_MAX


def follow_users(users: List[User]) -> List[User]:
    def follow_user_failed(user: User):
        user.follow_fail_count += 1
        logger.warning(f"Failed to follow user: {user.login}")
        store.update_user(user)

    followed_count = 0

    for i, user in enumerate(users):
        logger.info(f"[{i + 1}/{len(users)}]Starting to follow user: {user.login}")

        if scheduler.state == 0:
            return followed_count

        try:
            is_followed = fetch_follow_user(user=user, token=settings.GITHUB_TOKEN)
            if is_followed:
                user.is_followed = True
                user.followed_at = datetime.now()
                store.update_user(user)
                followed_count += 1
                logger.success(f"Followed user: {user.login}")
            else:
                follow_user_failed(user)
        except RequestException as e:
            if e.response is None or e.response.status_code in [401, 403, 422]:
                follow_user_failed(user)
                raise e
            time.sleep(random.randint(2, 4))
            logger.warning(f"Failed to follow user: {user.login}, continuing...")
            continue

        time.sleep(random.randint(2, 4))

    return followed_count


@scheduler.scheduled_job(
    "interval",
    id="follower-bot",
    seconds=settings.JOB_INTERVAL,
    jitter=settings.JOB_JITTER,
    next_run_time=datetime.now() if settings.JOB_RUN_NOW else undefined,
)
@logger.catch(reraise=False)
def run_bot():
    logger.info("Starting bot...")

    if is_follow_limit_reached():
        logger.info(
            f"Maximum followed users reached: {store.followed_users_count}/{settings.FOLLOW_USER_MAX}"
        )
        scheduler.shutdown(wait=False)
        return

    follow_count = settings.JOB_FOLLOW_USER_BASE + random.randint(
        0, settings.JOB_FOLLOW_USER_JITTER
    )
    logger.debug(f"Follow count: {follow_count}")
    users, is_over = get_unfollowed_users(follow_count)
    followed_count = follow_users(users)
    logger.info(f"Followed {followed_count} users")

    if is_over:
        logger.info("Not enough unfollowed users, stopping job...")
        scheduler.shutdown(wait=False)
        return

    logger.info("Bot finished")


def main():
    scheduler.start()
    while len(scheduler.get_jobs()) > 0:
        time.sleep(0.5)


if __name__ == "__main__":
    main()
