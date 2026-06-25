from rag.ratelimit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_allows_under_limit():
    rl = RateLimiter(per_min=3, per_day=10, global_per_day=100, clock=FakeClock())
    assert rl.check("1.1.1.1") is None
    assert rl.check("1.1.1.1") is None


def test_blocks_per_minute_then_recovers():
    clock = FakeClock()
    rl = RateLimiter(per_min=2, per_day=10, global_per_day=100, clock=clock)
    assert rl.check("ip") is None
    assert rl.check("ip") is None
    assert rl.check("ip") is not None  # 3rd within a minute -> blocked
    clock.now += 61
    assert rl.check("ip") is None  # minute window passed


def test_per_ip_isolation():
    rl = RateLimiter(per_min=1, per_day=10, global_per_day=100, clock=FakeClock())
    assert rl.check("a") is None
    assert rl.check("a") is not None
    assert rl.check("b") is None  # different ip unaffected


def test_global_daily_cap():
    rl = RateLimiter(per_min=100, per_day=100, global_per_day=2, clock=FakeClock())
    assert rl.check("a") is None
    assert rl.check("b") is None
    assert rl.check("c") is not None  # global cap hit regardless of ip


def test_daily_window_resets():
    clock = FakeClock()
    rl = RateLimiter(per_min=100, per_day=1, global_per_day=100, clock=clock)
    assert rl.check("ip") is None
    assert rl.check("ip") is not None  # daily per-ip reached
    clock.now += 86401
    assert rl.check("ip") is None  # next day resets
