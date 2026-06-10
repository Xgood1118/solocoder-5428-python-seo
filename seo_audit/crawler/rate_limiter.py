import asyncio
import time
from collections import defaultdict
from typing import Dict


class DomainRateLimiter:
    def __init__(self, requests_per_second: int = 5):
        self.requests_per_second = requests_per_second
        self._domain_timestamps: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def wait(self, domain: str):
        async with self._lock:
            now = time.monotonic()
            timestamps = self._domain_timestamps[domain]
            while timestamps and now - timestamps[0] >= 1.0:
                timestamps.pop(0)
            if len(timestamps) >= self.requests_per_second:
                sleep_time = 1.0 - (now - timestamps[0])
                await asyncio.sleep(sleep_time)
                now = time.monotonic()
                while timestamps and now - timestamps[0] >= 1.0:
                    timestamps.pop(0)
            timestamps.append(time.monotonic())
