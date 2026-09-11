"""Tiny issue tracker API; storage deliberately has no cache yet."""
from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)
    issues = {1: {"id": 1, "title": "Document the API", "status": "open"}}

    @app.get("/issues/<int:issue_id>")
    def get_issue(issue_id):
        issue = issues.get(issue_id)
        return (jsonify(issue), 200) if issue else (jsonify(error="not found"), 404)

    @app.patch("/issues/<int:issue_id>")
    def update_issue(issue_id):
        issue = issues.get(issue_id)
        if issue is None:
            return jsonify(error="not found"), 404
        data = request.get_json(silent=True) or {}
        if "title" in data:
            issue["title"] = data["title"]
        if "status" in data:
            issue["status"] = data["status"]
        return jsonify(issue)

    return app
