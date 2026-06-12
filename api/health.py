import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from api_logic import health_info
from lib.http import send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        send_json(self, health_info())
