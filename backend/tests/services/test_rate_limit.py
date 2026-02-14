"""Tests for the rate limiter."""

import pytest

from app.core.rate_limit import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.check("test") is True
        assert limiter.check("test") is True
        assert limiter.check("test") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.check("test") is True
        assert limiter.check("test") is True
        assert limiter.check("test") is False

    def test_different_keys_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.check("user1") is True
        assert limiter.check("user2") is True
        assert limiter.check("user1") is False
        assert limiter.check("user2") is False

    def test_window_expiry(self):
        import time
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.check("test") is True
        assert limiter.check("test") is False
        time.sleep(1.1)
        assert limiter.check("test") is True
