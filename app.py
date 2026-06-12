import os

from flask import Flask, jsonify, request, send_from_directory

from api_logic import create_round, health_info, process_guess

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(BASE, "public")

app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/style.css")
def style():
    return send_from_directory(PUBLIC, "style.css")


@app.get("/app.js")
def script():
    return send_from_directory(PUBLIC, "app.js")


@app.get("/api/health")
def health():
    return jsonify(health_info())


@app.post("/api/round")
def new_round():
    return jsonify(create_round())


@app.post("/api/guess")
def guess():
    data = request.get_json(silent=True) or {}
    body, code = process_guess(data.get("round_id"), data.get("guess"))
    return jsonify(body), code
