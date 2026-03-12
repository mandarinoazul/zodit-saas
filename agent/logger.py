import sys
from loguru import logger

# Remove the default logger
logger.remove()

# Add a formatted console logger
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    enqueue=True,  # thread-safe
)

# File logger for debugging and audit
logger.add(
    "logs/zodit_{time:YYYY-MM}.log",
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
    enqueue=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

def get_logger(name: str):
    return logger.bind(name=name)

# Expose the default logger
log = logger
