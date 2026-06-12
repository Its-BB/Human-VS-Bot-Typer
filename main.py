import os

from flask import Flask, jsonify, request, send_from_directory

from api_logic import create_round, health_info, process_guess

app = Flask(__name__, static_folder="public", static_url_path="")


@app.get("/")
def index():
    return send_from_directory("public", "index.html")


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
