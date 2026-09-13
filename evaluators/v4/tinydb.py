"""Behavioral regression from TinyDB #591 / PR #616; MIT license.

Copyright (C) 2013 Markus Siemens. See licenses/tinydb.txt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from tinydb.table import Document


for operation in ["update", "remove"]:
    for requested in [[99], [1, 99], [99, 2, 1]]:
        db = TinyDB(storage=MemoryStorage)
        db.insert_multiple({"value": 1} for _ in range(3))
        # Populate the query cache before writes.
        assert len(db.search(Query().value == 1)) == 3
        expected_ids = [identity for identity in requested if identity in [1, 2, 3]]
        try:
            if operation == "update":
                actual = db.update({"value": 9}, doc_ids=iter(requested))
            else:
                actual = db.remove(doc_ids=iter(requested))
        except Exception as error:
            raise AssertionError(f"{operation} with IDs {requested} must skip missing IDs, got {type(error).__name__}") from error
        assert actual == expected_ids, f"{operation} must return only affected IDs in request order"
        assert len(db.search(Query().value == 1)) == 3 - len(expected_ids), "writes must invalidate cached queries"
        assert db.get(doc_id=3)["value"] == 1, "unselected records must stay unchanged"
        db.close()

db = TinyDB(storage=MemoryStorage)
db.insert({"value": 1})
calls = []
assert db.update(lambda doc: calls.append(doc) or doc.update(value=2), doc_ids=[99, 1]) == [1]
assert len(calls) == 1 and db.get(doc_id=1)["value"] == 2
assert db.upsert(Document({"value": 3}, doc_id=20)) == [20]
assert db.get(doc_id=20)["value"] == 3
assert db.upsert(Document({"value": 4}, doc_id=20)) == [20]
assert len(db) == 2 and db.get(doc_id=20)["value"] == 4
print("PASS: missing/mixed IDs, generator IDs, affected lists, cache invalidation, callbacks, upsert")
