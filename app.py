from flask import Flask, Response, jsonify, request

from web_assets import FILES, TYPES

app = Flask(__name__)


@app.get("/")
@app.get("/index.html")
def index():
    return Response(FILES["index.html"], mimetype=TYPES["index.html"])


@app.get("/style.css")
def style():
    return Response(FILES["style.css"], mimetype=TYPES["style.css"])


@app.get("/app.js")
def script():
    return Response(FILES["app.js"], mimetype=TYPES["app.js"])


@app.get("/api/health")
def health():
    from api_logic import health_info
    return jsonify(health_info())


@app.post("/api/round")
def new_round():
    from api_logic import create_round
    return jsonify(create_round())


@app.post("/api/guess")
def guess():
    from api_logic import process_guess
    data = request.get_json(silent=True) or {}
    body, code = process_guess(data.get("round_id"), data.get("guess"))
    return jsonify(body), code
