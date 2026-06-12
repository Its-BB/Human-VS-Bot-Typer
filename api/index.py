import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from api_logic import create_round, health_info, process_guess
from lib.http import read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0].rstrip("/") == "/api/health":
            send_json(self, health_info())
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        if path == "/api/round":
            send_json(self, create_round())
        elif path == "/api/guess":
            data = read_json(self)
            body, code = process_guess(data.get("round_id"), data.get("guess"))
            send_json(self, body, code)
        else:
            self.send_error(404)
