from http.server import BaseHTTPRequestHandler

from api_logic import create_round
from lib.http import send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        send_json(self, create_round())

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
