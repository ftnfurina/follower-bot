import signal
import time

from apscheduler.events import EVENT_SCHEDULER_SHUTDOWN
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from .banner import print_banner
from .bots import FollowerBot, FollowingBot
from .log import init_logging
from .settings import get_settings
from .store import Store

settings = get_settings()
store = Store(url=settings.database.url, log_level=settings.database.log_level)

scheduler = BackgroundScheduler()
scheduler.add_listener(lambda _: store.close(), EVENT_SCHEDULER_SHUTDOWN)

init_logging(settings.loguru_config_file)
print_banner(settings.banner_file)


def signal_handler(_signal, _frame):
    logger.info("Received signal, shutting down scheduler...")
    scheduler.shutdown(wait=False)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

FollowingBot(settings=settings, store=store, scheduler=scheduler).join_scheduler()
FollowerBot(settings=settings, store=store, scheduler=scheduler).join_scheduler()


def main():
    jobs = scheduler.get_jobs()
    if len(jobs) == 0:
        logger.info("No jobs are enabled, exiting...")
        return

    scheduler.start()
    while len(scheduler.get_jobs()) > 0:
        time.sleep(0.5)


if __name__ == "__main__":
    main()
