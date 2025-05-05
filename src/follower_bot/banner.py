import os

from loguru import logger

from .file import read_file


def print_banner(banner_file: str) -> None:
    if not os.path.exists(banner_file):
        return
    logger.opt(raw=True).success(read_file(banner_file))
