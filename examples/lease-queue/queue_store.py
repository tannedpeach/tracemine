"""Simple scan-based durable-state model for a worker lease queue."""

from copy import deepcopy


class Queue:
    def __init__(self):
        self.jobs = {}
        self.sequence = 0

    def submit(self, key, payload, ready_at=0):
        if key in self.jobs:
            if self.jobs[key]["payload"] != payload:
                raise ValueError("idempotency conflict")
            return False
        self.sequence += 1
        self.jobs[key] = dict(
            payload=deepcopy(payload),
            ready=ready_at,
            order=self.sequence,
            generation=0,
            state="pending",
            deadline=None,
        )
        return True

    def claim(self, now, ttl):
        if ttl <= 0:
            raise ValueError("positive ttl required")
        eligible = [
            (job["ready"], job["order"], key)
            for key, job in self.jobs.items()
            if (job["state"] == "pending" and job["ready"] <= now)
            or (job["state"] == "leased" and job["deadline"] <= now)
        ]
        if not eligible:
            return None
        _, _, key = min(eligible)
        job = self.jobs[key]
        job.update(state="leased", generation=job["generation"] + 1, deadline=now + ttl)
        return key, job["generation"], deepcopy(job["payload"])

    def finish(self, key, generation, now, retry_at=None):
        job = self.jobs[key]
        if job["state"] != "leased" or generation != job["generation"] or now >= job["deadline"]:
            raise ValueError("stale lease")
        job["deadline"] = None
        if retry_at is None:
            job["state"] = "done"
        else:
            job.update(state="pending", ready=retry_at)

    def dump(self):
        return deepcopy({"sequence": self.sequence, "jobs": self.jobs})

    @classmethod
    def restore(cls, data):
        queue = cls()
        queue.jobs = deepcopy(data["jobs"])
        queue.sequence = data["sequence"]
        return queue
