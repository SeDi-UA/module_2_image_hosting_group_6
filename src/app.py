# app.py
import logging
import http.server
import socketserver
from pathlib import Path
import json
from urllib.parse import urlparse, parse_qs

from config import SERVER_PORT, EXTERNAL_PORT, MAX_FILES, MAX_REQUEST_SIZE, CONTENT_TYPES, UPLOAD_DIR, BASE_DIR
from file_handler import validate_and_save
from logger_config import logger
from database import db_manager


class ImageServerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.debug("%s - - %s" % (self.address_string(), format % args))

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        routes = {
            '/': lambda: self.server_response('form/index.html'),
            '/upload': lambda: self.server_response('form/upload.html'),
            '/images': lambda: self.server_response('form/images.html'),
            '/api/images': self.handle_get_images
        }

        if path in routes:
            routes[path]()
        elif path.startswith(('/static/', '/images/')):
            self.server_response(path)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/upload':
            logger.debug("POST /upload request received")
            self.handle_upload()
        else:
            logger.error(f"Unknown POST path: {self.path}")
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path.startswith('/api/delete'):
            self.handle_delete()
        else:
            logger.error(f"Unknown DELETE path: {path}")
            self.send_response(404)
            self.end_headers()

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def get_content(self, content_type, content_length):
        try:
            raw_data = self.rfile.read(content_length)

            boundary = content_type.split("boundary=")[1].encode()
            parts = raw_data.split(b'--' + boundary)

            uploaded_files = []
            counter = 0

            for part in parts:
                if counter > MAX_FILES:
                    logger.warning(f"Too many files, aborting")
                    return False, f"Too many files! Maximum allowed is {MAX_FILES} per request."

                if b'Content-Disposition' in part and b'name="images"' in part:
                    headers_part, body_part = part.split(b'\r\n\r\n', 1)

                    filename = ""
                    for line in headers_part.decode('utf-8', errors='ignore').split('\r\n'):
                        if 'filename=' in line:
                            filename = line.split('filename=')[1].strip('"')

                    if body_part.endswith(b'\r\n'):
                        file_bytes = body_part[:-2]
                    else:
                        file_bytes = body_part

                    if filename:
                        uploaded_files.append({
                            "bytes": file_bytes,
                            "filename": filename
                        })
                        counter += 1

            return True, uploaded_files

        except Exception as e:
            logger.error(e, exc_info=logger.isEnabledFor(logging.DEBUG))
            return False, "No files uploaded or data is corrupted"

    def handle_upload(self):
        content_length = int(self.headers.get('Content-Length', 0))

        if content_length > MAX_REQUEST_SIZE:
            logger.warning("Request entity too large, aborting")
            self.send_json_response(413, {
                "status": "error",
                "message": "Request entity too large!"
            })
            return

        content_type = self.headers.get('Content-Type', '')

        if not content_type.startswith('multipart/form-data'):
            logger.error(f"Unsupported Content-Type: {content_type}")
            self.send_json_response(400, {"status": "error", "message": "Expected multipart/form-data"})
            return

        is_files, result = self.get_content(content_type, content_length)

        if not is_files:
            msg = result
            self.send_json_response(400, {"status": "error", "message": msg})
            return

        response_files = []
        invalid_files = 0

        for file_data in result:
            file_bytes = file_data["bytes"]
            filename = file_data["filename"]

            is_valid, message, unique_name = validate_and_save(file_bytes, filename)

            if is_valid:
                file_size = len(file_bytes)
                file_type = Path(filename).suffix.lstrip('.').lower() or "unknown"

                db_success = db_manager.save_image_metadata(
                    unique_name=unique_name,
                    filename=filename,
                    size=file_size,
                    file_type=file_type
                )

                if db_success:
                    logger.debug(f"File {filename} ({unique_name}) successfully saved to disk and DB")
                    response_files.append({
                        "filename": filename,
                        "url": f"/images/{unique_name}"
                    })
                else:
                    logger.error(f"File {filename} saved to disk, but DB metadata saving failed")
                    invalid_files += 1
            else:
                logger.warning(f"File {filename} failed server validation: {message}")
                invalid_files += 1

        if not response_files:
            logger.info("All uploaded files failed validation or DB saving.")
            self.send_json_response(400, {"status": "error", "message": "All uploaded files failed validation or DB saving."})
            return

        logger.debug(f"Uploaded files: {response_files}")
        self.send_json_response(200, {
            "status": "success",
            "files": response_files,
            "invalid_files": invalid_files
        })

    def handle_get_images(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        try:
            page = int(params.get('page', [1])[0])
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        limit = 10
        offset = (page - 1) * limit

        db_images = db_manager.get_images(limit=limit, offset=offset)
        total_count = db_manager.get_total_images_count()

        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

        formatted_images = []
        for img in db_images:
            formatted_images.append({
                "id": img["id"],
                "filename": img["filename"],
                "url": f"/images/{img['unique_name']}",
                "size_kb": round(img["size"] / 1024, 2),
                "upload_time": img["upload_time"].strftime("%Y-%m-%d %H:%M:%S") if img.get("upload_time") else "",
                "file_type": img["file_type"],
            })

        self.send_json_response(200, {
            "status": "success",
            "images": formatted_images,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        })

    def handle_delete(self):
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            image_id = None

            if 'id' in params:
                image_id = int(params['id'][0])

            if not image_id:
                logger.error(f"No image ID provided in delete request: {self.path}")
                self.send_json_response(400, {"status": "error", "message": "Missing or invalid image ID"})
                return

            unique_name = db_manager.delete_image(image_id)

            if not unique_name:
                logger.warning(f"Image ID {image_id} not found in DB")
                self.send_json_response(404, {"status": "error", "message": "Image not found in DB"})
                return

            file_path = UPLOAD_DIR / unique_name
            if UPLOAD_DIR.resolve() in file_path.resolve().parents and file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"File {unique_name} (ID: {image_id}) successfully deleted from disk and DB")
                self.send_json_response(200, {"status": "success", "message": f"Image {image_id} deleted"})
            else:
                logger.warning(f"File {unique_name} was deleted from DB, but was not found on disk")
                self.send_json_response(200, {"status": "success", "message": f"Metadata for image {image_id} deleted"})

        except Exception as e:
            logger.error(e, exc_info=True)
            self.send_json_response(500, {"status": "error", "message": "Internal server error"})

    def server_response(self, path):
        try:
            if path.startswith("/images"):
                file_path = BASE_DIR / path.lstrip('/')
            else:
                file_path = Path(__file__).parent / path.lstrip('/')

            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"server_response: File {path} not found on server")
                self.send_response(404)
                self.end_headers()
                return

            content = file_path.read_bytes()

            self.send_response(200)
            content_type = CONTENT_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(len(content)))

            if path.startswith('images/'):
                self.send_header('Cache-Control', 'public, max-age=3600')

            try:
                self.end_headers()
                self.wfile.write(content)
            except ConnectionError as e:
                logger.debug(f"Client disconnected early while serving {path}: {e}")

        except FileNotFoundError as e:
            logger.error(e, exc_info=True)
            self.send_response(500)
            self.end_headers()

def run_server(port):
    if not db_manager.test_connection():
        logger.sys("CRITICAL: Database connection failed! Check PostgreSQL service.")
    else:
        if not db_manager.init_db():
            logger.sys("WARNING: Could not initialize database tables!")

    try:
        with socketserver.TCPServer(("", port), ImageServerHandler) as httpd:
            logger.sys(f"Backend service initialized on internal port {port}")

            if EXTERNAL_PORT != port:
                logger.sys(f"👉 Access the application via proxy at: http://localhost:{EXTERNAL_PORT}")
            else:
                logger.sys(f"👉 Access the application locally at: http://localhost:{port}")

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.sys(f"Server stopped by user")
    except OSError as e:
        if e.errno == 48:
            logger.sys(f"Port {port} is already in use. Please stop the server | lsof -ti :{port} | xargs kill -9")
        else:
            logger.sys(f"Error starting server: {e}")


if __name__ == "__main__":
    run_server(SERVER_PORT)