import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from api_logic import create_round
from lib.http import send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        send_json(self, create_round())
