import abc
from datetime import datetime
from functools import wraps
from typing import Generic, Literal, Optional, TypeVar, Union

from apscheduler.schedulers.base import STATE_STOPPED, BaseScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import undefined
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..email import Email
from ..model import CreateBy, History, HistoryState
from ..settings import Settings
from ..store import Store


class BotTriggerInterval(BaseModel):
    mode: Literal["interval"] = Field(default="interval", description="Interval mode")
    weeks: int = Field(default=0, ge=0, description="Weeks")
    days: int = Field(default=0, ge=0, description="Days")
    hours: int = Field(default=0, ge=0, description="Hours")
    minutes: int = Field(default=0, ge=0, description="Minutes")
    seconds: int = Field(default=0, ge=0, description="Seconds")
    jitter: Optional[int] = Field(
        default=None, ge=0, description="Jitter for the interval trigger"
    )
    timezone: Optional[str] = Field(
        default=None, description="Timezone for the trigger"
    )


class BotTriggerCron(BaseModel):
    mode: Literal["cron"] = Field(default="cron", description="Cron mode")
    expr: str = Field(description="Cron expression for the trigger")
    timezone: Optional[str] = Field(
        default=None, description="Timezone for the trigger"
    )


BotTrigger = Union[BotTriggerInterval, BotTriggerCron]


class BotSettings(BaseModel):
    name: str = Field(default="Bot", description="Bot name")
    enabled: bool = Field(default=True, description="Whether the bot is enabled")
    trigger: BotTrigger = Field(
        default_factory=BotTriggerInterval, description="Bot trigger settings"
    )
    immediately: bool = Field(
        default=False, description="Whether to execute the bot immediately after start"
    )


def create_trigger(trigger: BotTrigger) -> BaseTrigger:
    if trigger.mode == "cron":
        return CronTrigger.from_crontab(expr=trigger.expr, timezone=trigger.timezone)
    elif trigger.mode == "interval":
        return IntervalTrigger(
            weeks=trigger.weeks,
            days=trigger.days,
            hours=trigger.hours,
            minutes=trigger.minutes,
            seconds=trigger.seconds,
            jitter=trigger.jitter,
            timezone=trigger.timezone,
        )


def inject_session(func):
    @wraps(func)
    def wrapper(self: "Bot", *args, **kwargs):
        with Session(self.store.engine) as session:
            try:
                return func(self, *args, session=session, **kwargs)
            except Exception as e:
                logger.exception(f"Error executing {self.name} bot: {e}")
                session.rollback()
                raise e

    return wrapper


def inject_state(func):
    @wraps(func)
    def wrapper(self: "Bot", *args, **kwargs):
        session = kwargs.get("session")
        if session is None:
            raise ValueError("Session is not provided")

        state = self.store.query_state(session=session)

        try:
            return func(self, *args, state=state, **kwargs)
        except Exception as e:
            logger.exception(f"Error executing {self.name} bot: {e}")
            raise e
        finally:
            self.store.upsert(model=state, session=session)

    return wrapper


def inject_history(create_by: CreateBy):
    def decorator(func):
        @wraps(func)
        def wrapper(self: "Bot", *args, **kwargs):
            session = kwargs.get("session")
            if session is None:
                raise ValueError("Session is not provided")

            history = History(create_by=create_by, state=HistoryState.SUCCESS)

            try:
                return func(self, *args, history=history, **kwargs)
            except Exception as e:
                logger.exception(f"Error executing {self.name} bot: {e}")
                history.state = HistoryState.FAIL
                history.message = str(e)
                raise e
            finally:
                history.end_date = datetime.now()
                self.store.upsert(model=history, session=session)

        return wrapper

    return decorator


T = TypeVar("T", bound=BotSettings)


class Bot(abc.ABC, Generic[T]):
    name: str = "Bot"

    def __init__(
        self,
        settings: T,
        g_settings: Settings,
        store: Store,
        email: Optional[Email],
        scheduler: BaseScheduler,
    ):
        self.settings = settings
        self.g_settings = g_settings
        self.store = store
        self.email = email
        self.scheduler = scheduler
        self.id = f"{self.name}:{id(self)}"

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    @property
    def stopped(self) -> bool:
        return self.scheduler.state == STATE_STOPPED

    def generate_timestamp(self, default: Optional[int] = None) -> int:
        return int(datetime.now().timestamp()) if default is None else default

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)

    def join_scheduler(self) -> None:
        self.scheduler.add_job(
            self.exec,
            trigger=create_trigger(self.settings.trigger),
            id=self.id,
            name=self.name,
            misfire_grace_time=60,
            next_run_time=datetime.now() if self.settings.immediately else undefined,
        )

    def stop(self) -> None:
        self.scheduler.remove_job(self.id)

    @inject_session
    @abc.abstractmethod
    def exec(self, session: Session) -> None:
        raise NotImplementedError()
