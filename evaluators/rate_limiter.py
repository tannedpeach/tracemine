"""Immutable final evaluator for the rate-limiter live candidate."""

import importlib.util
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("candidate_limiter", root / "limiter.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class Clock:
    now = 0.0


clock = Clock()
limiter = module.RateLimiter(clock=lambda: clock.now)
assert limiter.allow("a")
clock.now = 1.0
assert limiter.allow("a")
clock.now = 2.0
assert limiter.allow("a")
clock.now = 9.999
assert not limiter.allow("a")
clock.now = 10.0
assert not limiter.allow("a"), "a sliding window must retain 1.0 and 2.0"
clock.now = 11.0
assert limiter.allow("a"), "the oldest accepted request expires at 11.0"
assert limiter.allow("b")
print("immutable rate-limiter evaluator passed")
