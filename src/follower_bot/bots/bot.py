import random
import time
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.base import STATE_STOPPED, BaseScheduler

from ..model import History, HistoryState, HistoryType
from ..settings import Settings
from ..store import Store


def inject_history(history_type: HistoryType):
    def decorator(func):
        @wraps(func)
        def wrapper(self: "Bot", *args, **kwargs):
            history = History()
            history.start_date = datetime.now()
            history.type = history_type
            try:
                result = func(self, *args, **kwargs, history=history)
                history.state = HistoryState.SUCCESS
                return result
            except Exception as e:
                history.state = HistoryState.FAIL
                history.message = str(e)
                raise e
            finally:
                history.end_date = datetime.now()
                self.store.add_history(history)

        return wrapper

    return decorator


class Bot:
    def __init__(self, settings: Settings, store: Store, scheduler: BaseScheduler):
        self.settings = settings
        self.store = store
        self.scheduler = scheduler

    def is_stopped(self) -> bool:
        return self.scheduler.state == STATE_STOPPED

    def sleep(self, min: int = 2, max: int = 4):
        time.sleep(random.randint(min, max))

    def shutdown(self):
        self.scheduler.shutdown(wait=False)

    def join_scheduler(self):
        raise NotImplementedError()

    def exec(self, history: History):
        raise NotImplementedError()
