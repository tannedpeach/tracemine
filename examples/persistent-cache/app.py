"""Tiny issue tracker API with a per-app issue cache."""
from copy import deepcopy
from threading import RLock
from time import monotonic

from flask import Flask, jsonify, request


def _load_issue(issues, issue_id):
    return deepcopy(issues.get(issue_id))


def create_app():
    app = Flask(__name__)
    issues = {1: {"id": 1, "title": "Document the API", "status": "open"}}
    cache = {}
    lock = RLock()

    @app.get("/issues/<int:issue_id>")
    def get_issue(issue_id):
        with lock:
            now = monotonic()
            cached = cache.get(issue_id)
            if cached is not None and now < cached[0]:
                issue = cached[1]
            else:
                cache.pop(issue_id, None)
                issue = _load_issue(issues, issue_id)
                if issue is not None:
                    cache[issue_id] = (now + 60, issue)
            return (jsonify(issue), 200) if issue else (jsonify(error="not found"), 404)

    @app.patch("/issues/<int:issue_id>")
    def update_issue(issue_id):
        with lock:
            issue = issues.get(issue_id)
            if issue is None:
                return jsonify(error="not found"), 404
            data = request.get_json(silent=True) or {}
            if "title" in data:
                issue["title"] = data["title"]
            if "status" in data:
                issue["status"] = data["status"]
            cache.pop(issue_id, None)
            return jsonify(issue)

    return app
