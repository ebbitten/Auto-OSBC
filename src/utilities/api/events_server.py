import http.server
import json
import threading
from typing import Any


class EventsAPIHandler(http.server.BaseHTTPRequestHandler):
    cache: dict[str, Any] = {}

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))

        # Extract the endpoint from the path
        endpoint = self.path.strip("/").split("/")[-1]

        # Store the data in the cache
        self.__class__.cache[endpoint] = data["data"]

        self.send_response(200)
        self.end_headers()

        print(f"Received data for endpoint: {endpoint}")

    def log_message(self, format, *args):
        # Suppress default logging
        return


def run_server(port=8081):
    server_address = ("", port)
    httpd = http.server.HTTPServer(server_address, EventsAPIHandler)
    print(f"EventsAPI Server running on port {port}")
    httpd.serve_forever()


def start_server_thread():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread


# Initialize cache with empty dictionaries for each expected endpoint
EventsAPIHandler.cache = {"player_status": {}, "inventory_items": {}, "equipment_items": {}, "skills": {}}
