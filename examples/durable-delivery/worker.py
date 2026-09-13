"""Ordered delivery, with committed messages retained for audit."""

from copy import deepcopy


class Worker:
    def __init__(self, storage, send):
        self.storage, self.send = storage, send

    def enqueue(self, payload):
        state = self.storage.load()
        identity = state["next_id"]
        state["next_id"] += 1
        state["messages"].append({"id": identity, "payload": deepcopy(payload), "done": False})
        self.storage.save(state)
        return identity

    def drain(self):
        state = self.storage.load()
        delivered = 0
        for message in state["messages"]:
            if message["done"]:
                continue
            self.send(str(message["id"]), deepcopy(message["payload"]))
            message["done"] = True
            self.storage.save(state)
            delivered += 1
        return delivered
