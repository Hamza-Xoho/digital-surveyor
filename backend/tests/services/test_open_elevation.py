"""Tests for the open elevation fallback service."""

from app.services.open_elevation import _haversine_m


class TestHaversine:
    def test_same_point(self):
        assert _haversine_m(51.5, -0.1, 51.5, -0.1) == 0.0

    def test_known_distance(self):
        # London to Brighton is roughly 85 km
        d = _haversine_m(51.5074, -0.1278, 50.8225, -0.1372)
        assert 75_000 < d < 80_000

    def test_short_distance(self):
        # ~111 m for 0.001 degrees latitude
        d = _haversine_m(51.5, -0.1, 51.501, -0.1)
        assert 100 < d < 120
