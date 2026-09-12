import random

import pytest

from queue_store import Queue


def test_expiry_fencing_retry_and_stable_order():
    queue = Queue()
    queue.submit("a", {"items": [1]}, 0)
    queue.submit("b", {}, 0)
    key, token, payload = queue.claim(0, 5)
    assert key == "a"
    payload["items"].append(2)
    assert queue.claim(1, 5)[0] == "b"
    assert queue.claim(4.999, 5) is None
    assert queue.claim(5, 5) == ("a", token + 1, {"items": [1]})
    with pytest.raises(ValueError):
        queue.finish("a", token, 5)
    queue.finish("a", token + 1, 6, retry_at=20)
    assert queue.claim(6, 3)[0] == "b"
    assert queue.claim(7, 3) is None
    assert queue.claim(9, 30)[0] == "b"
    assert queue.claim(20, 5)[0] == "a"


def test_invalid_transitions_do_not_change_state_and_done_cannot_repeat():
    queue = Queue()
    queue.submit("a", [])
    before = queue.dump()
    with pytest.raises(ValueError):
        queue.claim(0, 0)
    assert queue.dump() == before
    _, token, _ = queue.claim(0, 5)
    leased = queue.dump()
    with pytest.raises(ValueError):
        queue.finish("a", token, 5)
    assert queue.dump() == leased
    _, newer, _ = queue.claim(5, 5)
    queue.finish("a", newer, 6)
    assert queue.claim(100, 5) is None
    assert queue.submit("a", []) is False
    with pytest.raises(ValueError):
        queue.submit("a", ["different"])


def test_restore_preserves_leases_tokens_payloads_and_future_order():
    queue = Queue()
    for key in ["z", "a", "m"]:
        queue.submit(key, {"list": []}, 2)
    assert queue.claim(2, 10)[0] == "z"
    data = queue.dump()
    restored = Queue.restore(data)
    data["jobs"]["a"]["payload"]["list"].append(1)
    assert restored.claim(3, 10) == ("a", 1, {"list": []})
    assert queue.claim(3, 10) == ("a", 1, {"list": []})
    assert restored.claim(12, 10)[0] == "z"


@pytest.mark.parametrize("seed", range(12))
def test_claim_selection_matches_scan_contract(seed):
    randomizer = random.Random(seed)
    queue = Queue()
    for number in range(24):
        queue.submit(str(number), [number], randomizer.randrange(12))
    for now in range(50):
        state = queue.dump()
        eligible = [
            (j["ready"], j["order"], key)
            for key, j in state["jobs"].items()
            if (j["state"] == "pending" and j["ready"] <= now)
            or (j["state"] == "leased" and j["deadline"] <= now)
        ]
        claimed = queue.claim(now, 4)
        assert (claimed[0] if claimed else None) == (min(eligible)[2] if eligible else None)
        if claimed and randomizer.randrange(3):
            queue.finish(
                claimed[0],
                claimed[1],
                now + 0.5,
                retry_at=now + 7 if randomizer.randrange(2) else None,
            )
        if now % 7 == 0:
            queue = Queue.restore(queue.dump())
