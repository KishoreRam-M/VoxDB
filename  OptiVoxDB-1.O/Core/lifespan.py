"""FastAPI lifespan management."""

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI

from Core.Logging import logger
from Core.Config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup/shutdown.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("🚀 OptiVox DB starting up...")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Debug mode: {settings.debug}")

    # Create necessary directories
    directories = [
        settings.backup_output_dir,
        settings.logs_dir,
        settings.exports_dir
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
        logger.info(f"Directory ready: {directory}")

    # Initialize AI service
    from services.ai_service import ai_service
    if ai_service.is_available():
        logger.info("✅ Gemini AI service initialized")
    else:
        logger.warning("⚠️ Gemini AI service not available")

    logger.info("✅ OptiVox DB ready")

    yield

    # Shutdown
    logger.info("🛑 OptiVox DB shutting down...")

    # Close database connections
    from db.engine import close_all_engines
    close_all_engines()

    # Close AI service
    ai_service.close()

    logger.info("✅ Shutdown complete")
