# logger_config.py
import logging

from config.config import LOG_DIR, LOG_FILE_PATH, LOG_LEVEL

LOG_DIR.mkdir(exist_ok=True)


logging.addLevelName(45, "SYSTEM")

def logger_system(self, message, *args, **kws):
    if self.isEnabledFor(45):
        self._log(45, message, args, **kws)

logging.Logger.sys = logger_system

def setup_logger(level_name):
    level = getattr(logging, level_name.upper(), logging.INFO)

    logger = logging.getLogger("ImageServer")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)-7s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger(LOG_LEVEL)