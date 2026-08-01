# config.py
import os
from pathlib import Path


SERVER_PORT = 8000
EXTERNAL_PORT = int(os.getenv("EXTERNAL_PORT", SERVER_PORT))

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

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / 'images')))

LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / 'logs')))
LOG_FILE_PATH = Path(os.getenv("LOG_FILE_PATH", str(LOG_DIR / 'server.log')))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

#'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_LEVEL = 'DEBUG'