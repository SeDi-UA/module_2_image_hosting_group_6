import http.server
import socketserver
from pathlib import Path
import os
import json
import io
import re


class ImageServerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {
            '/': 'form/index.html',
            '/upload': 'form/upload.html',
            '/images-list': 'form/images.html'
        }

        if self.path in routes:
            self.server_response(routes[self.path])
        elif self.path.startswith('/static/'):
            self.server_response(self.path)
            # self.serve_static(self.path)
        # elif self.path.startswith('/api/images'):
        #     self.handle_get_images()
        else:
            self.send_response(404)
            self.end_headers()

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