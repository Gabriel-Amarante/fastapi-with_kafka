import logging
import os
from functools import lru_cache
from typing import List

from pydantic import BaseSettings

log = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    """Class for storing settings."""

    kafka_host: str = os.getenv("KAFKA_HOST")
    kafka_port: str = os.getenv("KAFKA_PORT")
    kafka_topics: str = os.getenv("KAFKA_TOPICS")
    kafka_instance = f"{kafka_host}:{kafka_port}"
    file_encoding: str = "utf-8"
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")


@lru_cache()
def get_settings() -> BaseSettings:
    """Get application settings usually stored as environment variables.

    Returns:
        Settings: Application settings.
    """
    log.info("Loading config settings from the environment...")
    return Settings()
