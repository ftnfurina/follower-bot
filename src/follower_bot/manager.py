import importlib.util
import inspect
import json
import os
from typing import Dict, List, Optional, Tuple, Type, Union

import yaml
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_SCHEDULER_SHUTDOWN,
    JobExecutionEvent,
)
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from pydantic import RootModel, create_model

from .bots import Bot, BotSettings
from .email import BotError, Email
from .file import read_file, write_file
from .settings import Settings
from .store import Store

BOTS_SCHEMA_FILE = ".vscode/bots-schema.json"


class Manager:
    def __init__(self, settings: Settings, store: Store, email: Optional[Email] = None):
        self.settings = settings
        self.store = store
        self.email = email

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_listener(
            self._handle_scheduler_shutdown, EVENT_SCHEDULER_SHUTDOWN
        )
        self._scheduler.add_listener(self._handle_job_error, EVENT_JOB_ERROR)

        self._bot_classes: Dict[str, Tuple[Type[Bot], Type[BotSettings]]] = {}
        self._scan_classes()
        self._generate_bots_yaml_schema()

        self._bots: List[Bot] = []
        self._bots_settings: List[BotSettings] = []
        self._read_bots_settings()
        self._register_bots()

    def _scan_classes(self) -> None:
        bots_dir = os.path.join(os.path.dirname(__file__), "bots")
        for root, _, files in os.walk(bots_dir):
            root_name = os.path.basename(root)
            if root_name.startswith("__"):
                continue

            for file in files:
                if not file.endswith(".py") or file.startswith("__"):
                    continue

                module_name = file[:-3]
                module_path = os.path.join(root, file)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    logger.exception(f"Failed to load module {module_name}: {e}")
                    continue

                bot_class, bot_settings_class = None, None

                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Bot) and obj != Bot:
                        logger.debug(f"Found bot class {obj.name}")
                        bot_class = obj
                    elif issubclass(obj, BotSettings) and obj != BotSettings:
                        bot_settings_class = obj

                if bot_class and bot_settings_class:
                    self._bot_classes[bot_class.name] = (bot_class, bot_settings_class)

    def _register_bots(self) -> None:
        for settings in self._bots_settings:
            if settings.name not in self._bot_classes:
                logger.warning(f"No bot found with name {settings.name}")
                continue
            bot_class, bot_settings_class = self._bot_classes[settings.name]
            bot = bot_class(
                settings=bot_settings_class(**settings.model_dump()),
                g_settings=self.settings,
                store=self.store,
                email=self.email,
                scheduler=self._scheduler,
            )
            self._bots.append(bot)

    def _generate_bots_yaml_schema(self) -> None:
        bot_settings_classes = [
            settings_class for _, settings_class in self._bot_classes.values()
        ]
        Bots_Type = List[Union[tuple(bot_settings_classes)]]
        Bots = create_model("Bots", __base__=RootModel, root=Bots_Type)

        json_schema = json.dumps(Bots.model_json_schema(), indent=2)

        write_file(BOTS_SCHEMA_FILE, json_schema, newline="\n")

    def _read_bots_settings(self) -> None:
        bots_file = self.settings.bots_file
        if not os.path.exists(bots_file):
            raise ValueError(f"Settings file {bots_file} does not exist")

        try:
            bots = yaml.safe_load(read_file(bots_file))
            if not isinstance(bots, list):
                bots = []

            for bot in bots:
                bot_settings = BotSettings(**bot)
                if bot_settings.name not in self._bot_classes:
                    logger.warning(f"No bot found with name {bot_settings.name}")
                    continue
                _, bot_settings_class = self._bot_classes[bot_settings.name]

                self._bots_settings.append(bot_settings_class(**bot))

        except Exception as e:
            raise ValueError(f"Failed to parse settings file {bots_file}: {e}")

    def _handle_scheduler_shutdown(self, _) -> None:
        self.close()

    def _handle_job_error(self, event: JobExecutionEvent) -> None:
        if self.email is None or not self.settings.enabled_error_email:
            logger.debug(f"Skipping error email for job {event.job_id}")
            return

        ok, error = self.email.send_error(
            BotError(
                name=event.job_id,
                message=str(event.exception),
                traceback=event.traceback,
            )
        )
        if not ok:
            logger.error(f"Failed to send error email for job {event.job_id}: {error}")
        else:
            logger.debug(f"Sent error email for job {event.job_id}")

    @property
    def running_count(self) -> int:
        return len(self._scheduler.get_jobs())

    def start(self) -> None:
        for bot in self._bots:
            if not bot.enabled:
                logger.debug(f"Skipping disabled bot {bot.name}")
                continue
            bot.join_scheduler()

        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown()

    def close(self) -> None:
        self.store.close()
