"""Centralized logging configuration with UTF-8 support."""

import sys
import logging
from pathlib import Path
from datetime import datetime
from Core.Config import settings   # ✅ Correct import

class UTF8StreamHandler(logging.StreamHandler):
    """Custom handler ensuring UTF-8 encoding on Windows."""

    def __init__(self, stream=None):
        super().__init__(stream)
        if sys.platform == "win32" and stream is None:
            self.setStream(sys.stdout)

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            safe_msg = self.format(record).encode('ascii', 'ignore').decode('ascii')
            stream = self.stream
            stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging() -> logging.Logger:
    """Configure logging with file and console handlers."""
    logs_dir = Path(settings.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("OptiVox_DB")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    if logger.handlers:
        return logger

    log_file = logs_dir / f"vox_db_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    console_handler = UTF8StreamHandler()
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


logger = setup_logging()
