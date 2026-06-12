from http.server import BaseHTTPRequestHandler

from api_logic import process_guess
from lib.http import read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = read_json(self)
        body, code = process_guess(data.get("round_id"), data.get("guess"))
        send_json(self, body, code)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
