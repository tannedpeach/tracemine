"""Deterministic transport ambiguity and durable acknowledgement failure checks."""

import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from worker import Worker


class Storage:
    def __init__(self):
        self.data = {"next_id": 1, "messages": []}
        self.fail_ack = False

    def load(self):
        return deepcopy(self.data)

    def save(self, state):
        if self.fail_ack and any(m["done"] for m in state["messages"]):
            self.fail_ack = False
            raise OSError("acknowledgement write failed")
        self.data = deepcopy(state)


store, effects, calls = Storage(), {}, []
failures = [True, True, False]


def send(key, payload):
    calls.append((key, deepcopy(payload)))
    effects.setdefault(key, deepcopy(payload))
    payload.append("transport mutation")
    if failures and failures.pop(0):
        raise TimeoutError("response lost after remote commit")


worker = Worker(store, send)
worker.enqueue([1])
worker.enqueue([2])
assert worker.drain(max_attempts=2) == 0, "exhaustion must stop before acknowledging or sending later messages"
assert [key for key, _ in calls] == ["1", "1"]
assert not any(m["done"] for m in store.data["messages"])
worker = Worker(store, send)
assert worker.drain(max_attempts=2) == 2, "restart must retry the pending message and then advance"
assert [key for key, _ in calls] == ["1", "1", "1", "2"]
assert effects == {"1": [1], "2": [2]}, "stable message keys let the receiver deduplicate effects"
assert calls == [(key, [int(key)]) for key, _ in calls], "each send needs a fresh payload copy"
assert worker.drain(max_attempts=2) == 0

store = Storage()
calls = []
worker = Worker(store, lambda key, payload: calls.append(key))
worker.enqueue([1])
worker.enqueue([2])
store.fail_ack = True
try:
    worker.drain(max_attempts=3)
except OSError:
    pass
else:
    raise AssertionError("durable acknowledgement failures must propagate")
assert calls == ["1"], "storage errors must not enter the transport retry loop or advance ordering"
assert Worker(store, lambda key, payload: calls.append(key)).drain(max_attempts=3) == 2
assert calls == ["1", "1", "2"]

for invalid in [0, -1, True, 1.5]:
    before = deepcopy((store.data, calls))
    try:
        worker.drain(max_attempts=invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("max_attempts must be a positive non-bool integer")
    assert (store.data, calls) == before

store = Storage()
worker = Worker(store, lambda key, payload: (_ for _ in ()).throw(ValueError("permanent")))
worker.enqueue([1])
try:
    worker.drain(max_attempts=3)
except ValueError:
    pass
else:
    raise AssertionError("non-transient transport errors must propagate")
assert not store.data["messages"][0]["done"]
print("PASS: ambiguous success, ordering, restart, stable keys, payload isolation, ack failure, validation")
