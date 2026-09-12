"""Correct snapshot-based transaction reference, intended for small local stores."""

from copy import deepcopy


class Conflict(Exception):
    pass


class Store:
    def __init__(self, records):
        self.records = deepcopy(records)
        self.cache = {}

    def read(self, key):
        if key not in self.cache:
            self.cache[key] = deepcopy(self.records[key])
        return deepcopy(self.cache[key])

    def apply(self, operations, persist=lambda key, record: None):
        """Apply sequential optimistic writes atomically to local records and cache.

        persist is a validation/staging callback which may raise; it must not commit
        external state itself. None stages deletion. Version checks observe earlier
        operations in this batch. Missing records have version 0.
        """
        before = deepcopy((self.records, self.cache))
        results = []
        try:
            for operation in operations:
                key, expected = operation["key"], operation["expected"]
                current = self.records.get(key)
                if (current["version"] if current else 0) != expected:
                    raise Conflict(key)
                if operation["kind"] == "delete":
                    self.records.pop(key, None)
                    self.cache.pop(key, None)
                    persist(key, None)
                    results.append(None)
                elif operation["kind"] == "put":
                    record = {"version": expected + 1, "value": deepcopy(operation["value"])}
                    self.records[key] = record
                    self.cache[key] = deepcopy(record)
                    persist(key, deepcopy(record))
                    results.append(deepcopy(record))
                else:
                    raise ValueError("unknown operation")
            return results
        except Exception:
            self.records, self.cache = before
            raise
