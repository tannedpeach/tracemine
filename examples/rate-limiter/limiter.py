"""Existing fixed-window limiter to migrate to rolling-window semantics."""

from time import monotonic


class RateLimiter:
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.windows = {}

    def allow(self, client):
        bucket = int(self.clock() // 10)
        previous, count = self.windows.get(client, (bucket, 0))
        if previous != bucket:
            count = 0
        if count >= 3:
            return False
        self.windows[client] = (bucket, count + 1)
        return True
