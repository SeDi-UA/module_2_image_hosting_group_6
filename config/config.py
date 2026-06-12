# config.py
from pathlib import Path


SERVER_PORT = 8000

BASE_DIR = Path(__file__).parent.parent

MAX_FILES = 10
MAX_REQUEST_SIZE = 50 * 1024 * 1024
CONTENT_TYPES = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.html': 'text/html'
        }

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024

UPLOAD_DIR = BASE_DIR / 'images'

LOG_DIR = BASE_DIR / 'logs'
LOG_FILE_PATH = LOG_DIR / 'server.log'

#'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_LEVEL = 'DEBUG'