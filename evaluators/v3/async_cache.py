"""Evaluator-owned deterministic schedules. No live services or wall-clock sleeps."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from cache import Cache


async def turns():
    for _ in range(20):
        await asyncio.sleep(0)


class Loader:
    def __init__(self):
        self.calls = []
        self.cancelled = []

    async def __call__(self, key):
        future = asyncio.get_running_loop().create_future()
        index = len(self.calls)
        self.calls.append((key, future))
        try:
            return await future
        except asyncio.CancelledError:
            self.cancelled.append(index)
            raise


async def scenario():
    loader, now = Loader(), [0]
    cache = Cache(loader, ttl=10, clock=lambda: now[0])
    first = asyncio.create_task(cache.get("a"))
    second = asyncio.create_task(cache.get("a"))
    other = asyncio.create_task(cache.get("b"))
    await turns()
    assert [k for k, _ in loader.calls] == ["a", "b"], "one load per key; unrelated keys must progress"
    first.cancel()
    await asyncio.gather(first, return_exceptions=True)
    assert not loader.calls[0][1].cancelled(), "cancelling one waiter must preserve the shared load"
    now[0] = 50
    loader.calls[0][1].set_result({"value": [1]})
    loader.calls[1][1].set_result({"value": [2]})
    await turns()
    assert second.done() and other.done(), "completed loads must release waiters"
    second.result()["value"].append("caller")
    now[0] = 59
    assert await cache.get("a") == {"value": [1]}, "TTL starts at completion; returned values must be detached"
    now[0] = 60
    old = asyncio.create_task(cache.get("a"))
    await turns()
    assert len(loader.calls) == 3, "the exact TTL boundary must expire"
    cache.invalidate("a")
    new = asyncio.create_task(cache.get("a"))
    await turns()
    assert len(loader.calls) == 4, "post-invalidation callers must start a new generation"
    loader.calls[3][1].set_result({"value": [4]})
    await turns()
    loader.calls[2][1].set_result({"value": [3]})
    await turns()
    assert old.result() == {"value": [3]} and new.result() == {"value": [4]}
    assert await cache.get("a") == {"value": [4]}, "old completion must not replace the new cached value"

    cache.invalidate("a")
    abandoned = asyncio.create_task(cache.get("a"))
    await turns()
    abandoned.cancel()
    await asyncio.gather(abandoned, return_exceptions=True)
    await turns()
    assert 4 in loader.cancelled, "last waiter cancellation must release the loader"
    retry = asyncio.create_task(cache.get("a"))
    await turns()
    assert len(loader.calls) == 6, "abandoned flights must not trap later callers"
    loader.calls[5][1].set_exception(ValueError("upstream rejected"))
    await turns()
    assert isinstance(retry.exception(), ValueError), "loader errors must propagate"
    again = asyncio.create_task(cache.get("a"))
    peer = asyncio.create_task(cache.get("a"))
    await turns()
    assert len(loader.calls) == 7, "failed flights must be evicted and new callers coalesced"
    loader.calls[6][1].set_result({"value": [7]})
    await turns()
    again.result()["value"].append(8)
    assert peer.result() == {"value": [7]}, "coalesced callers must receive independent mutable values"
    print("PASS: coalescing, parallel keys, cancellation, generation fencing, TTL, errors, alias isolation")


asyncio.run(scenario())
