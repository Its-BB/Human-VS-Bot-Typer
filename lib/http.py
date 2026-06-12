import json
from http.server import BaseHTTPRequestHandler


def read_json(h: BaseHTTPRequestHandler) -> dict:
    n = int(h.headers.get("Content-Length", 0))
    if not n:
        return {}
    return json.loads(h.rfile.read(n))


def send_json(h: BaseHTTPRequestHandler, data: dict, status: int = 200) -> None:
    body = json.dumps(data).encode()
    h.send_response(status)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(body)))
    h.end_headers()
    h.wfile.write(body)
