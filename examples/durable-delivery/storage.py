"""Small atomic JSON state file for a single synchronous delivery worker."""

import json
import os
from pathlib import Path


class StateFile:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {"next_id": 1, "messages": []}
        return json.loads(self.path.read_text())

    def save(self, state):
        temporary = self.path.with_suffix(".tmp")
        try:
            with temporary.open("w") as output:
                json.dump(state, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
