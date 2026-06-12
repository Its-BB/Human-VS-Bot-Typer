import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request

from api_logic import create_round, health_info, process_guess

app = Flask(__name__)


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
