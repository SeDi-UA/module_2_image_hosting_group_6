import os
import subprocess
from datetime import datetime
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Налаштування змінних
CONTAINER_NAME = "postgres_db"
DB_USER = "pgPyAdmin"
DB_NAME = "images_db"
BACKUP_DIR = "backups"

def create_backup():
    # Перевірка та створення папки backups
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Генерація імені файлу з часовою міткою
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    # Формування команди pg_dump
    command = f"docker exec -t {CONTAINER_NAME} pg_dump -U {DB_USER} -d {DB_NAME}"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            result = subprocess.run(
                command,
                shell=True,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        print(f"[SUCCESS] Резервну копію успішно створено: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Помилка створення бекапу: {e.stderr}")

if __name__ == "__main__":
    create_backup()