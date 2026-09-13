from storage import StateFile
from worker import Worker


def test_order_persistence_and_transport_isolation(tmp_path):
    delivered = []

    def send(key, payload):
        delivered.append((key, list(payload)))
        payload.append("transport")

    store = StateFile(tmp_path / "state.json")
    worker = Worker(store, send)
    payload = [1]
    assert worker.enqueue(payload) == 1
    payload.append("caller")
    assert worker.enqueue([2]) == 2
    assert worker.drain() == 2
    assert delivered == [("1", [1]), ("2", [2])]
    assert Worker(store, send).drain() == 0
    assert store.load()["messages"][0]["payload"] == [1]
