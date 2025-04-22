import os

from loguru import logger


def print_banner(banner_file: str):
    if not os.path.exists(banner_file):
        return
    with open(banner_file, "r") as f:
        logger.opt(raw=True).success(f.read())
