"""Core module initialization."""

from Core.Config import settings, get_settings
from Core.Logging import logger
from Core.lifespan import lifespan
from Core.middleware import RequestLoggingMiddleware

__all__ = [
    "settings",
    "get_settings",
    "logger",
    "lifespan",
    "RequestLoggingMiddleware",
]
