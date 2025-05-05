import signal
import time

from loguru import logger

from .banner import print_banner
from .email import Email
from .log import init_logging
from .manager import Manager
from .settings import get_settings
from .store import Store

settings = get_settings()

init_logging(settings.loguru_config_file)
print_banner(settings.banner_file)

store = Store(url=settings.database.url, log_level=settings.database.log_level)
email = None if settings.email is None else Email(settings.email)
manager = Manager(settings=settings, store=store, email=email)


def signal_handler(_signal, _frame) -> None:
    logger.info("Received signal, shutting down scheduler...")
    manager.shutdown()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    manager.start()
    while manager.running_count > 0:
        time.sleep(0.5)
    manager.close()


if __name__ == "__main__":
    main()
