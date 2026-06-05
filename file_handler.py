import io
import uuid
from pathlib import Path
from PIL import Image

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024
UPLOAD_DIR = Path('images')


UPLOAD_DIR.mkdir(exist_ok=True)


def check_image(file, file_ext): #Pillow
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Недозволений формат файлу. Очікувалися: {', '.join(ALLOWED_EXTENSIONS)}"
    try:
        image_stream = io.BytesIO(file)
        with Image.open(image_stream) as img:
            img.verify()
        return True, None
    except Exception:
        return False, "Не вдалося прочитати файл"


def check_size(file_size):
    if file_size > MAX_FILE_SIZE:
        return False, "Файл занадто великий (максимум 5 МБ)"
    return True, None


def validate_file(file, filename):
    is_valid_size, msg = check_size(len(file))
    if not is_valid_size:
        return False, msg, None
    ext = Path(filename).suffix.lower()
    is_image, msg = check_image(file, ext)
    if not is_image:
        return False, msg, None
    try:
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / unique_name
        with open(file_path, 'wb') as f:
            f.write(file)
        return True, "Files saved successfully! Go to the Images tab to view them.", unique_name
    except Exception as e:
        return False, str(e), None


