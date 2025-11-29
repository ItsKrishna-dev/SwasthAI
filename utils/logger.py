from loguru import logger
import sys
from config import settings

def setup_logger():
    """Configure logger"""
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    
    # File logging
    logger.add(
        settings.BASE_DIR / "logs" / "swasthai_{time}.log",
        rotation="500 MB",
        retention="10 days",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
    )
    
    return logger

log = setup_logger()
