import time
from typing import Optional


class SeatsCache:
    def __init__(self, ttl_seconds: int = 30) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[list[str], float]] = {}

    def get(self, event_id: str) -> Optional[list[str]]:
        entry = self._cache.get(event_id)
        if entry is None:
            return None
        seats, timestamp = entry
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[event_id]
            return None
        return seats

    def set(self, event_id: str, seats: list[str]) -> None:
        self._cache[event_id] = (seats, time.monotonic())


seats_cache = SeatsCache(ttl_seconds=30)