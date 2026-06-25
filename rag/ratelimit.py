import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """In-memory multi-tier limiter. Single-process (one container) is enough
    for the demo. Returns None when allowed, else a human-readable reason."""

    def __init__(self, per_min=5, per_day=40, global_per_day=600, clock=time.time):
        self.per_min = per_min
        self.per_day = per_day
        self.global_per_day = global_per_day
        self._clock = clock
        self._lock = Lock()
        self._minute = defaultdict(list)
        self._day = defaultdict(int)
        self._day_idx = None
        self._global = 0

    def _roll_day(self, now):
        idx = int(now // 86400)
        if idx != self._day_idx:
            self._day_idx = idx
            self._day.clear()
            self._global = 0

    def check(self, ip):
        with self._lock:
            now = self._clock()
            self._roll_day(now)
            if self._global >= self.global_per_day:
                return "daily budget reached, try again tomorrow"
            if self._day[ip] >= self.per_day:
                return "daily limit per visitor reached"
            recent = [t for t in self._minute[ip] if now - t < 60]
            if len(recent) >= self.per_min:
                return "too many requests, please slow down"
            recent.append(now)
            self._minute[ip] = recent
            self._day[ip] += 1
            self._global += 1
            return None
