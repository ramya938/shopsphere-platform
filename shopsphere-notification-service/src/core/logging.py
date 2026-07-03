import sys
import logging
from loguru import logger
from src.config import settings

class InterceptHandler(logging.Handler):
    """
    Intercepts standard library logging calls and routes them to Loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    # Remove loguru default logger
    logger.remove()

    # Intercept logs from other loggers (e.g. uvicorn)
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL)

    # Disable other loggers' default handlers to avoid duplicate output
    for logger_name in ("uvicorn.error", "uvicorn.access"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

    # Configure Loguru output
    if settings.ENVIRONMENT == "production":
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    logger.info(f"Logging configured successfully with level: {settings.LOG_LEVEL}")
