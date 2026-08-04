# database.py
import psycopg2
from psycopg2.extras import RealDictCursor

from logger_config import logger
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT


class DatabaseManager:
    def _get_connection(self):
        """Створює та повертає підключення до бази даних"""
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

    def test_connection(self):
        """Перевірка з'єднання з базою даних при старті додатка"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    db_version = cursor.fetchone()
                    logger.info(f"Successfully connected to PostgreSQL. Version: {db_version[0]}")
                    return True
        except Exception as e:
            if isinstance(e, psycopg2.OperationalError):
                try:
                    err_msg = str(e).encode('raw_unicode_escape').decode('cp1251', errors='replace')
                    logger.error(f"Database connection failed: {err_msg}")
                    return False
                except Exception:
                    pass
            logger.error(f"Database connection failed: {e}")
            return False

    def init_db(self):
        """Створює необхідні таблиці в БД, якщо вони ще не існують"""
        query = """
            CREATE TABLE IF NOT EXISTS images (
                id SERIAL PRIMARY KEY,
                unique_name TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                size INTEGER NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_type TEXT NOT NULL
            );
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    conn.commit()
                    logger.info("Database initialized successfully (tables checked/created).")
                    return True
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
            return False

    def save_image_metadata(self, unique_name, filename, size, file_type):
        """Зберігає метадані зображення у базу даних"""
        query = """
            INSERT INTO images (unique_name, filename, size, file_type)
            VALUES (%s, %s, %s, %s);
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (unique_name, filename, size, file_type))
                    conn.commit()
                    logger.info(f"Image metadata saved to DB for file: {filename} ({unique_name})")
                    return True
        except Exception as e:
            logger.error(f"Failed to save image metadata to DB: {e}")
            return False

    def get_images(self, limit=10, offset=0):
        """Отримує список зображень з пагінацією, відсортований від новіших до старіших."""
        query = """
            SELECT id, unique_name, filename, size, upload_time, file_type
            FROM images
            ORDER BY upload_time DESC
            LIMIT %s OFFSET %s;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (limit, offset))
                    images = cursor.fetchall()
                    return images
        except Exception as e:
            logger.error(f"Failed to fetch images list from DB: {e}")
            return []

    def get_total_images_count(self):
        """Отримує загальну кількість зображень у базі (для розрахунку кількості сторінок)."""
        query = "SELECT COUNT(*) FROM images;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    return count
        except Exception as e:
            logger.error(f"Failed to count images in DB: {e}")
            return 0

    def delete_image(self, image_id):
        """Видаляє запис про зображення з БД та повертає unique_name для видалення з диска."""
        query = "DELETE FROM images WHERE id = %s RETURNING unique_name;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (image_id,))
                    result = cursor.fetchone()
                    conn.commit()
                    if result:
                        logger.info(f"Image entry with ID {image_id} deleted from DB")
                        return result[0]
                    return False
        except Exception as e:
            logger.error(f"Failed to delete image with ID {image_id} from DB: {e}")
            return False

db_manager = DatabaseManager()