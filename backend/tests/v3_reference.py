"""Test-only implementations for checking evaluator expectations, never live evidence."""

import asyncio
from copy import deepcopy
from time import monotonic
from uuid import uuid4


class Cache:
    def __init__(self, loader, ttl=10, clock=monotonic):
        self.loader, self.ttl, self.clock = loader, ttl, clock
        self.values, self.flights = {}, {}

    def invalidate(self, key):
        self.values.pop(key, None)
        self.flights.pop(key, None)

    async def get(self, key):
        cached = self.values.get(key)
        if cached is not None and self.clock() < cached[0]:
            return deepcopy(cached[1])
        flight = self.flights.get(key)
        if flight is None:
            flight = {"waiters": 0}

            async def load():
                try:
                    value = await self.loader(key)
                    if self.flights.get(key) is flight:
                        self.values[key] = (self.clock() + self.ttl, deepcopy(value))
                    return value
                finally:
                    if self.flights.get(key) is flight:
                        self.flights.pop(key)

            flight["task"] = asyncio.create_task(load())
            self.flights[key] = flight
        flight["waiters"] += 1
        try:
            return deepcopy(await asyncio.shield(flight["task"]))
        finally:
            flight["waiters"] -= 1
            if not flight["waiters"] and not flight["task"].done():
                if self.flights.get(key) is flight:
                    self.flights.pop(key)
                flight["task"].cancel()
                await asyncio.gather(flight["task"], return_exceptions=True)


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

    def drain(self, max_attempts=1):
        if type(max_attempts) is not int or max_attempts <= 0:
            raise ValueError("invalid attempts")
        state = self.storage.load()
        count = 0
        for message in state["messages"]:
            if message["done"]:
                continue
            for attempt in range(max_attempts):
                try:
                    self.send(str(message["id"]), deepcopy(message["payload"]))
                except (TimeoutError, ConnectionError):
                    if attempt + 1 == max_attempts:
                        return count
                else:
                    break
            message["done"] = True
            self.storage.save(state)
            count += 1
        return count


class Catalog:
    def __init__(self):
        self.records, self.cursors = {}, {}

    def put(self, identity, created_at, payload):
        self.records[identity] = {
            "id": identity,
            "created_at": created_at,
            "payload": deepcopy(payload),
        }

    def delete(self, identity):
        self.records.pop(identity, None)

    def list(self):
        return deepcopy(sorted(self.records.values(), key=lambda r: (r["created_at"], r["id"])))

    def page(self, limit=20, cursor=None):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid limit")
        if cursor is None:
            rows, offset = self.list(), 0
        else:
            if not isinstance(cursor, str) or cursor not in self.cursors:
                raise ValueError("unknown cursor")
            rows, offset = self.cursors[cursor]
        end = offset + limit
        token = None
        if end < len(rows):
            # Stable reuse matters because the entire response is replayable.
            for known, (prior, position) in self.cursors.items():
                if prior is rows and position == end:
                    token = known
                    break
            if token is None:
                token = uuid4().hex
                self.cursors[token] = (rows, end)
        return {"items": deepcopy(rows[offset:end]), "next_cursor": token}
