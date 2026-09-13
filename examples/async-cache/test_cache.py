import asyncio

from service import MetadataService


def test_ttl_invalidation_and_value_isolation():
    async def scenario():
        now, calls = [0], []

        async def loader(key):
            calls.append(key)
            return {"items": [len(calls)]}

        service = MetadataService(loader, lambda: now[0])
        value = await service.fetch("a")
        value["items"].append(99)
        assert await service.fetch("a") == {"items": [1]}
        now[0] = 10
        assert await service.fetch("a") == {"items": [2]}
        service.changed("a")
        assert await service.fetch("a") == {"items": [3]}
        assert await service.fetch("b") == {"items": [4]}
    asyncio.run(scenario())
