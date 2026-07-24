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
            logger.error(f"Database connection failed: {e}")
            return False

    def save_image_metadata(self, filename, original_name, size, file_type):
        """Зберігає метадані зображення у базу даних"""
        query = """
            INSERT INTO images (filename, original_name, size, file_type)
            VALUES (%s, %s, %s, %s);
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (filename, original_name, size, file_type))
                    conn.commit()
                    logger.info(f"Image metadata saved to DB for file: {original_name} ({filename})")
                    return True
        except Exception as e:
            logger.error(f"Failed to save image metadata to DB: {e}")
            return False

    def get_images(self, limit=10, offset=0):
        """Отримує список зображень з пагінацією, відсортований від новіших до старіших."""
        query = """
            SELECT id, filename, original_name, size, upload_time, file_type
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
        """Видаляє запис про зображення з БД та повертає filename для видалення з диска."""
        query = "DELETE FROM images WHERE id = %s RETURNING filename;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (image_id,))
                    result = cursor.fetchone()
                    conn.commit()
                    if result:
                        logger.info(f"Image entry with ID {image_id} deleted from DB")
                        return result[0]
                    return None
        except Exception as e:
            logger.error(f"Failed to delete image with ID {image_id} from DB: {e}")
            return False