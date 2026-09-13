"""Behavioral regression from cachetools #405 and its accepted fix; MIT license.

Copyright (c) 2014-2026 Thomas Kemmer. See licenses/cachetools.txt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
import cachetools


factories = [
    cachetools.Cache, cachetools.FIFOCache, cachetools.LRUCache,
    cachetools.LFUCache, cachetools.RRCache,
    lambda **kw: cachetools.TTLCache(ttl=100, timer=lambda: 0, **kw),
    lambda **kw: cachetools.TLRUCache(ttu=lambda k, v, now: 100, timer=lambda: 0, **kw),
]
for factory in factories:
    for replacement in [7, 4, 1]:
        cache = factory(maxsize=10, getsizeof=lambda value: value)
        cache[3], cache[4] = 3, 4
        cache[4] = replacement
        actual = dict(cache)
        expected = {3: 3, 4: replacement}
        assert actual == expected, f"{type(cache).__name__} replacing 4 with {replacement}: expected {expected}, got {actual}"
        assert cache.currsize == 3 + replacement, "replacement accounting must match stored values"

# Deterministic eviction policies can select the key currently being replaced.
for factory in [cachetools.FIFOCache, cachetools.LRUCache]:
    cache = factory(maxsize=10, getsizeof=lambda value: value)
    cache["old"], cache["other"] = 3, 4
    cache["old"] = 9
    assert dict(cache) == {"old": 9}, "a replaced eviction victim must still reserve enough space"
    assert cache.currsize == 9
    cache["small"] = 1
    assert cache.currsize == 10 and len(cache) == 2
print("PASS: grow, shrink, same-size replacement across seven caches; eviction-victim accounting")
