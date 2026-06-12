import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from http.server import BaseHTTPRequestHandler

from api_logic import create_round, health_info, process_guess
from lib.http import read_json, send_json

_assets_path = os.path.join(os.path.dirname(__file__), "_assets.py")
_spec = importlib.util.spec_from_file_location("_assets", _assets_path)
_assets = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_assets)
FILES = _assets.FILES
TYPES = _assets.TYPES

ROUTES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/style.css": "style.css",
    "/app.js": "app.js",
}


def _norm(path: str) -> str:
    p = path.split("?")[0].split("#")[0]
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/") or "/"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = _norm(self.path)
        if path == "/api/health":
            send_json(self, health_info())
            return
        name = ROUTES.get(path)
        if not name or name not in FILES:
            self.send_error(404)
            return
        body = FILES[name].encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", TYPES[name])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = _norm(self.path)
        if path == "/api/round":
            send_json(self, create_round())
        elif path == "/api/guess":
            data = read_json(self)
            body, code = process_guess(data.get("round_id"), data.get("guess"))
            send_json(self, body, code)
        else:
            self.send_error(404)

    def log_message(self, *_):
        pass
