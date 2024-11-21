from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import mimetypes
import urllib.parse
import os
from jinja2 import Environment, FileSystemLoader


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.send_read_page()
        else:
            self.send_static(pr_url.path[1:])

    def do_POST(self):
        content_type = self.headers.get("Content-Type")
        length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(length)

        if content_type == "application/x-www-form-urlencoded":
            decoded_data = urllib.parse.unquote_plus(post_data.decode("utf-8"))
            post_data = urllib.parse.parse_qs(decoded_data)
            username = post_data.get("username")
            message = post_data.get("message")
            if username and message:
                self.process_message(username[0], message[0])
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Bad request")

        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Unsupported Content-Type")

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        file_path = self.get_file_path(filename)
        with open(file_path, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self, filename, status=200):
        file_path = self.get_file_path(filename)
        if not os.path.exists(file_path):
            self.send_html_file("error.html", 404)
            return

        self.send_response(status)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(file_path, "rb") as fd:
            self.wfile.write(fd.read())

    def get_file_path(self, filename):
        return os.path.join(os.path.dirname(__file__), filename)

    def process_message(self, username, message):
        data = {}
        timestamp = datetime.now().isoformat()  # type: ignore
        entry = {"username": username, "message": message}

        if os.path.exists("storage/data.json"):
            try:
                with open("storage/data.json", "r") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = {}
        data[timestamp] = entry

        os.makedirs("storage", exist_ok=True)
        with open("storage/data.json", "w") as file:
            json.dump(data, file, indent=4)

        self.send_response(302)
        self.send_header("Location", "/read")
        self.end_headers()

    def send_read_page(self):
        if os.path.exists("storage/data.json"):
            try:
                with open("storage/data.json", "r") as file:
                    messages = json.load(file)
            except json.JSONDecodeError:
                messages = {}
        else:
            messages = {}

        if messages:
            formatted_messages = {
                datetime.fromisoformat(timestamp).strftime("%Y-%m-%dT%H:%M:%S"): entry
                for timestamp, entry in messages.items()
            }
        else:
            formatted_messages = {}

        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("read.html")
        content = template.render(messages=formatted_messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 8000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
