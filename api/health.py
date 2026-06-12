from http.server import BaseHTTPRequestHandler

from api_logic import health_info
from lib.http import send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        send_json(self, health_info())
