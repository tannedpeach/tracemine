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
