from limiter import RateLimiter


def test_three_requests_then_rejection():
    limiter = RateLimiter(clock=lambda: 1.0)
    assert [limiter.allow("a") for _ in range(4)] == [True, True, True, False]


def test_client_and_instance_isolation():
    first, second = RateLimiter(clock=lambda: 1.0), RateLimiter(clock=lambda: 1.0)
    for _ in range(3):
        assert first.allow("a")
    assert not first.allow("a")
    assert first.allow("b")
    assert second.allow("a")


def test_long_idle_period():
    now = [1.0]
    limiter = RateLimiter(clock=lambda: now[0])
    for _ in range(3):
        assert limiter.allow("a")
    now[0] = 100.0
    assert limiter.allow("a")
