import http.server
import socketserver
from pathlib import Path

import json
from urllib.parse import urlparse, parse_qs

from file_handler import validate_file, UPLOAD_DIR

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


class ImageServerHandler(http.server.BaseHTTPRequestHandler):
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
            self.handle_upload()
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self ):
        if self.path.startswith('/api/delete'):
            self.handle_delete()
        else:
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
            # logging.error(f"Критична помилка сервера: {e}", exc_info=True)
            return False, "No files uploaded or data is corrupted"

    def handle_upload(self):
        content_length = int(self.headers.get('Content-Length', 0))

        if content_length > MAX_REQUEST_SIZE:
            self.send_json_response(413, {
                "status": "error",
                "message": "Request entity too large!"
            })
            return

        content_type = self.headers.get('Content-Type', '')

        if not content_type.startswith('multipart/form-data'):
            self.send_json_response(400, {"status": "error", "message": "Expected multipart/form-data"})
            return

        is_files, result = self.get_content(content_type, content_length)

        if not is_files:
            msg = result
            self.send_json_response(400, {"status": "error", "message": msg})
            return

        response_files = []

        for file_data in result:
            file_bytes = file_data["bytes"]
            filename = file_data["filename"]

            is_valid, message, unique_name = validate_file(file_bytes, filename)

            if is_valid:
                response_files.append({
                    "original_name": filename,
                    "url": f"/images/{unique_name}"
                })
            else:
                print(f"File {filename} failed server validation: {message}")

        if not response_files:
            self.send_json_response(400, {"status": "error", "message": "All uploaded files failed validation."})
            return

        self.send_json_response(200, {
            "status": "success",
            "files": response_files
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

        self.send_json_response(200, {"status": "success", "images": files})

    def handle_delete(self):
        try:
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            file_param = params.get('file')

            if not file_param:
                self.send_json_response(400, {"status": "error", "message": "Missing 'file' parameter"})
                return

            filename = file_param[0]
            file_path = UPLOAD_DIR / filename

            if UPLOAD_DIR.resolve() in file_path.resolve().parents and file_path.exists() and file_path.is_file():
                file_path.unlink()
                self.send_json_response(200, {"status": "success", "message": f"File {filename} deleted"})
            else:
                self.send_json_response(404, {"status": "error", "message": "File not found or access denied"})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": "Internal server error"})


    def server_response(self, path):
        try:
            file_path = Path(__file__).parent / path.lstrip('/')

            if not file_path.exists() or not file_path.is_file():
                self.send_response(404)
                self.end_headers()
                return

            content = file_path.read_bytes()

            self.send_response(200)
            content_type = CONTENT_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
            self.send_header('Content-type', content_type)

            if path.startswith('images/'):
                self.send_header('Cache-Control', 'public, max-age=3600')

            self.end_headers()
            self.wfile.write(content)

        except FileNotFoundError as e:
            self.send_response(500)
            self.end_headers()

def run_server(port=8000):
    try:
        with socketserver.TCPServer(("", port), ImageServerHandler) as httpd:
            print(f"Server running on port {port} ...", "http://localhost:8000/", sep="\n")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("Server stopped by user")
    except OSError as e:
        if e.errno == 48:
            print(f"Port {port} is already in use. Please stop the server | lsof -ti :{port} | xargs kill -9")
        else:
            print(f"Error starting server: {e}")


if __name__ == "__main__":
    run_server()