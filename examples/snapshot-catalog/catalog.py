"""Mutable issue catalog with detached reads and ordered current-state listing."""

from copy import deepcopy


class Catalog:
    def __init__(self):
        self.records = {}

    def put(self, identity, created_at, payload):
        self.records[identity] = {"id": identity, "created_at": created_at,
                                  "payload": deepcopy(payload)}

    def delete(self, identity):
        self.records.pop(identity, None)

    def list(self):
        return deepcopy(sorted(self.records.values(), key=lambda r: (r["created_at"], r["id"])))
