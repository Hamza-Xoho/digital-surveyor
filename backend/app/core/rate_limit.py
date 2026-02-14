"""Simple in-memory rate limiter for assessment endpoints.

No external dependencies required. Uses a sliding window approach
with automatic cleanup of expired entries.
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request

from app.core.config import settings


class RateLimiter:
    """Token-bucket style rate limiter keyed by client IP."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _cleanup(self, key: str, now: float) -> None:
        """Remove expired timestamps."""
        cutoff = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, key: str) -> bool:
        """Check if a request is allowed. Returns True if allowed."""
        now = time.time()
        with self._lock:
            self._cleanup(key, now)
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True

    def get_client_key(self, request: Request) -> str:
        """Extract client identifier from request."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"


# Assessment rate limiter: generous in dev/test, tighter in production
_max_req = 100 if settings.ENVIRONMENT == "local" else 10
assessment_limiter = RateLimiter(max_requests=_max_req, window_seconds=60)


async def check_assessment_rate_limit(request: Request) -> None:
    """FastAPI dependency to enforce rate limits on assessment endpoints."""
    key = assessment_limiter.get_client_key(request)
    if not assessment_limiter.check(key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before running another assessment.",
        )
