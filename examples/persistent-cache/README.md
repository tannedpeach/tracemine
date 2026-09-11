# Persistent cache task

This fixture starts with the actual cache implementation and tests produced by
recorded run `11ab0728156444b08799fe59b7e85d8f`. It extends the small Flask issue
tracker with a realistic next task: preserve caching while moving storage to
SQLite and keeping independent app instances coherent.

The code is an agent-produced starting point, not a hand-authored failure.
Run `python3 -m pytest -q` with the dependencies in requirements.txt installed.
