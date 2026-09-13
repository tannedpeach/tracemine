"""Sequential TTL cache used by an asynchronous metadata service."""

from copy import deepcopy
from time import monotonic


class Cache:
    def __init__(self, loader, ttl=10, clock=monotonic):
        self.loader, self.ttl, self.clock = loader, ttl, clock
        self.values = {}
        self.versions = {}

    def invalidate(self, key):
        self.versions[key] = self.versions.get(key, 0) + 1
        self.values.pop(key, None)

    async def get(self, key):
        cached = self.values.get(key)
        if cached is not None and self.clock() < cached[0]:
            return deepcopy(cached[1])
        version = self.versions.get(key, 0)
        value = await self.loader(key)
        if self.versions.get(key, 0) == version:
            self.values[key] = (self.clock() + self.ttl, deepcopy(value))
        return deepcopy(value)
