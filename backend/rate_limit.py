"""Sliding-window rate limiter, in-memory by default.

This is process-local (single-instance). For multi-pod deployments, swap the backend
for a Redis-backed implementation by overriding `_check_and_consume`.
"""
import logging
import os
import threading
import time
from collections import defaultdict, deque
from typing import Tuple
from fastapi import HTTPException, Request, status

log = logging.getLogger(__name__)

LOGIN_PER_MIN = int(os.environ.get("LOGIN_RATE_LIMIT_PER_MIN") or 10)
LOGIN_BURST = int(os.environ.get("LOGIN_RATE_LIMIT_BURST") or 5)


class SlidingWindowLimiter:
    def __init__(self, window_seconds: int, max_calls: int):
        self.window = window_seconds
        self.max_calls = max_calls
        self._buckets: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> Tuple[bool, int]:
        """Returns (allowed, retry_after_seconds)."""
        now = time.time()
        with self._lock:
            q = self._buckets[key]
            # Evict entries outside the window
            while q and (now - q[0]) > self.window:
                q.popleft()
            if len(q) >= self.max_calls:
                retry = max(1, int(self.window - (now - q[0])) + 1)
                return False, retry
            q.append(now)
            return True, 0

    def reset(self, key: str):
        with self._lock:
            self._buckets.pop(key, None)


# Global limiters
login_limiter = SlidingWindowLimiter(window_seconds=60, max_calls=LOGIN_PER_MIN)
login_burst_limiter = SlidingWindowLimiter(window_seconds=10, max_calls=LOGIN_BURST)


def _client_ip(request: Request) -> str:
    # Trust X-Forwarded-For when behind a proxy/ingress; fall back to request.client.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request) -> None:
    ip = _client_ip(request)
    ok, retry = login_burst_limiter.check(f"login:burst:{ip}")
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts (burst). Slow down.",
            headers={"Retry-After": str(retry)},
        )
    ok, retry = login_limiter.check(f"login:1m:{ip}")
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a minute.",
            headers={"Retry-After": str(retry)},
        )


def rate_limit_clear_login(request: Request) -> None:
    """Call on successful login to reset the burst counter for this IP (good UX)."""
    ip = _client_ip(request)
    login_burst_limiter.reset(f"login:burst:{ip}")
