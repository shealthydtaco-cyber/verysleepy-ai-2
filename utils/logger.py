import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(
    name: str = "verysleepy",
    level: int = logging.INFO,
) -> logging.Logger:
    from utils.config import load_config
    
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Prevent duplicate handlers

    config = load_config()
    level_name = config.get("system", {}).get("log_level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    logger.setLevel(level)

    # Ensure logs directory exists (use absolute path)
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler
    # maxBytes=5MB, backup_count=3 (keeps 3 backup files + 1 current = 4 total)
    file_handler = RotatingFileHandler(
        log_dir / "verysleepy.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
