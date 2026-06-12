import io
import uuid
from PIL import Image
from pathlib import Path

from config.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR

UPLOAD_DIR.mkdir(exist_ok=True)


def check_image(file, file_ext): #Pillow
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file format. Expected:{', '.join(ALLOWED_EXTENSIONS)}"
    try:
        image_stream = io.BytesIO(file)
        with Image.open(image_stream) as img:
            img.verify()
        return True, None
    except Exception:
        return False, "Failed to read file"


def check_size(file_size):
    if file_size > MAX_FILE_SIZE:
        return False, "File too large (maximum 5 MB)"
    return True, None


def validate_and_save(file, filename):
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
        return True, "Files saved successfully!", unique_name
    except Exception as e:
        return False, str(e), None
