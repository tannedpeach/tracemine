"""Evaluator-owned snapshot traversal checked against frozen list values."""

import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from catalog import Catalog
from api import Service


service = Service()
assert service.page_items(limit=1) == {"items": [], "next_cursor": None}
catalog = Catalog()
for identity in [9, 2, 7, 1, 8, 3]:
    catalog.put(identity, identity // 3, {"tags": [identity]})
frozen = catalog.list()
page = catalog.page(limit=2)
assert page["items"] == frozen[:2]
first_cursor = page["next_cursor"]
assert isinstance(first_cursor, str) and first_cursor
page["items"][0]["payload"]["tags"].append("caller")
for identity in [1, 2, 3, 7, 8, 9]:
    catalog.put(identity, -identity, {"tags": ["updated"]})
catalog.delete(7)
catalog.put(100, -100, {})
received = deepcopy(frozen[:2])
cursor = first_cursor
while cursor is not None:
    page = catalog.page(limit=1, cursor=cursor)
    assert catalog.page(limit=1, cursor=cursor) == page, "cursor replay must be repeatable"
    assert len(page["items"]) == 1
    received.extend(deepcopy(page["items"]))
    cursor = page["next_cursor"]
assert received == frozen, "later pages must retain original values, order, deleted rows and membership"
assert catalog.page(limit=100)["items"] == catalog.list(), "new traversals must see current records"
assert catalog.page(limit=2, cursor=first_cursor)["items"] == frozen[2:4]
other = Catalog()
for token in [first_cursor, "garbage", ""]:
    try:
        other.page(limit=1, cursor=token)
    except ValueError:
        pass
    else:
        raise AssertionError("foreign or malformed cursor must be rejected")
for limit in [0, -1, 101, True, 1.5, "2"]:
    try:
        catalog.page(limit=limit)
    except ValueError:
        pass
    else:
        raise AssertionError("limit must be an integer from 1 through 100, excluding bool")
assert Catalog().page(limit=2) == {"items": [], "next_cursor": None}
print("PASS: mutation-stable membership, values, order, replay, independent traversals, cursor scope, validation")
