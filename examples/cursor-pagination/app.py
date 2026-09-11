"""Small catalog API before pagination; caller owns the source item list."""

from copy import deepcopy

from flask import Flask, jsonify


def create_app(items):
    app = Flask(__name__)
    records = deepcopy(items)

    @app.get("/items")
    def get_items():
        return jsonify(items=sorted(records, key=lambda item: (item["created_at"], item["id"])))

    return app
