# app.py
import logging
import http.server
import socketserver
from pathlib import Path

import json
from urllib.parse import urlparse, parse_qs

from config.config import SERVER_PORT, MAX_FILES, MAX_REQUEST_SIZE, CONTENT_TYPES, UPLOAD_DIR
from file_handler import validate_and_save
from logger_config import logger


class ImageServerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.debug("%s - - %s" % (self.address_string(), format % args))

    def do_GET(self):
        routes = {
            '/': lambda: self.server_response('form/index.html'),
            '/upload': lambda: self.server_response('form/upload.html'),
            '/images': lambda: self.server_response('form/images.html'),
            '/api/images': self.handle_get_images
        }

        if self.path in routes:
            routes[self.path]()
        elif self.path.startswith(('/static/', '/images/')):
            self.server_response(self.path)
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

    def do_DELETE(self ):
        if self.path.startswith('/api/delete'):
            self.handle_delete()
        else:
            logger.error(f"Unknown DELETE path: {self.path}")
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
            logger.warning(f"Request entity too large, aborting")
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
                logger.debug(F"File {filename} successfully uploaded to server")
                response_files.append({
                    "original_name": filename,
                    "url": f"/images/{unique_name}"
                })
            else:
                logger.warning(f"File {filename} failed server validation: {message}")
                invalid_files += 1

        if not response_files:
            logger.info("All uploaded files failed validation.")
            self.send_json_response(400, {"status": "error", "message": "All uploaded files failed validation."})
            return

        # logger.debug(f"Uploaded files: {response_files}")
        self.send_json_response(200, {
            "status": "success",
            "files": response_files,
            "invalid_files": invalid_files
        })

    def handle_get_images(self):
        files = []

        if UPLOAD_DIR.exists():
            for f in UPLOAD_DIR.iterdir():
                files.append({
                    "name": f.name,
                    "url": f"/images/{f.name}"
                })
            files.sort(key=lambda x: (UPLOAD_DIR / x["name"]).stat().st_mtime, reverse=True)
        else:
            logger.debug("No upload directory found")

        self.send_json_response(200, {"status": "success", "images": files})

    def handle_delete(self):
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            file_param = params.get('file')

            if not file_param:
                logger.error(f"No file param found: {self.path}")
                self.send_json_response(400, {"status": "error", "message": "Missing 'file' parameter"})
                return

            filename = file_param[0]
            file_path = UPLOAD_DIR / filename

            if UPLOAD_DIR.resolve() in file_path.resolve().parents and file_path.exists() and file_path.is_file():
                logger.info(f"File {filename} successfully deleted from server")
                file_path.unlink()
                self.send_json_response(200, {"status": "success", "message": f"File {filename} deleted"})
            else:
                logger.warning(f"File {filename} not found on server")
                self.send_json_response(404, {"status": "error", "message": "File not found or access denied"})
        except Exception as e:
            logger.error(e, exc_info=True)
            self.send_json_response(500, {"status": "error", "message": "Internal server error"})

    def server_response(self, path):
        try:
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
    try:
        with socketserver.TCPServer(("", port), ImageServerHandler) as httpd:
            logger.sys(f"Server running on port {port}")
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