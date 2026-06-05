import http.server
import socketserver
from pathlib import Path
import os
import uuid

import json
import io
import re

from file_handler import validate_file


class ImageServerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {
            '/': 'form/index.html',
            '/upload': 'form/upload.html',
            '/images': 'form/images.html'
        }

        if self.path in routes:
            self.server_response(routes[self.path])
        elif self.path.startswith('/static/'):
            self.server_response(self.path)
            # self.serve_static(self.path)
        # elif self.path.startswith('/images'):
        #      self.handle_get_images()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/upload':
            # logging.info("Отримано запит POST /upload")
            self.handle_upload()
        else:
            self.send_response(404)
            self.end_headers()

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def get_content(self, content_type):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(content_length)

            boundary = content_type.split("boundary=")[1].encode()
            parts = raw_data.split(b'--' + boundary)

            file_bytes = b""
            filename = ""

            for part in parts:
                if b'Content-Disposition' in part and b'name="image"' in part:
                    headers_part, body_part = part.split(b'\r\n\r\n', 1)
                    for line in headers_part.decode('utf-8', errors='ignore').split('\r\n'):
                        if 'filename=' in line:
                            filename = line.split('filename=')[1].strip('"')
                    if body_part.endswith(b'\r\n'):
                        file_bytes = body_part[:-2]
                    else:
                        file_bytes = body_part
                    break

            return file_bytes, filename
        except Exception as e:
            # logging.error(f"Критична помилка сервера: {e}", exc_info=True)
            return None, None


    def handle_upload(self):
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_json_response(400, {"status": "error", "message": "Expected multipart/form-data"})
            return

        file_bytes, filename = self.get_content(content_type)

        if not file_bytes or not filename:
            self.send_json_response(400, {"status": "error", "message": "No file uploaded or data is corrupted"})
            return

        is_valid, message, unique_name = validate_file(file_bytes, filename)

        if is_valid:
            # logging.info(f"Файл {filename} успішно збережено як {unique_name}")
            response_body = {
                "status": "success",
                "message": message,
                "url": f"/images/{unique_name}"
            }
            self.send_json_response(200, response_body)
        else:
            # logging.warning(f"Валідація файлу {filename} провалена: {message}")
            self.send_json_response(400, {"status": "error", "message": message})

    def server_response(self, path):
        try:
            file_path = Path(__file__).parent / path.lstrip('/')
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header('Content-type', self.get_content_type(file_path.suffix))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def get_content_type(self, extension):
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.html': 'text/html'
        }
        return content_types.get(extension.lower(), 'application/octet-stream')

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