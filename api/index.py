import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
if not os.path.isdir(PUBLIC):
    PUBLIC = os.path.join(ROOT, "public")

from flask import Flask, jsonify, request, send_from_directory

from api_logic import create_round, health_info, process_guess

app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/app.js")
def app_js():
    return send_from_directory(PUBLIC, "app.js")


@app.get("/style.css")
def style_css():
    return send_from_directory(PUBLIC, "style.css")


@app.get("/api/health")
def health():
    return jsonify(health_info())


@app.post("/api/round")
def round():
    return jsonify(create_round())


@app.post("/api/guess")
def guess():
    data = request.get_json(silent=True) or {}
    body, code = process_guess(data.get("round_id"), data.get("guess"))
    return jsonify(body), code
