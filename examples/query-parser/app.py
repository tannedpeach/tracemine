from flask import Flask, jsonify, request
from query import tokenize


def create_app():
    app = Flask(__name__)

    @app.post("/parse")
    def parse():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or not isinstance(body.get("query"), str):
            return jsonify(error="query must be a string"), 400
        try:
            return jsonify(tokens=tokenize(body["query"]))
        except ValueError as error:
            return jsonify(error=str(error)), 400

    return app
