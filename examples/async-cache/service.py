"""The caller-facing adapter keeps cache ownership inside each service."""

from cache import Cache


class MetadataService:
    def __init__(self, loader, clock):
        self.cache = Cache(loader, ttl=10, clock=clock)

    async def fetch(self, key):
        return await self.cache.get(key)

    def changed(self, key):
        self.cache.invalidate(key)
