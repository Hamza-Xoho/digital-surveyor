"""Tests for LiDAR gradient classification."""

import pytest

from app.services.lidar import classify_gradient, GRADIENT_THRESHOLDS


class TestClassifyGradient:
    def test_flat_is_green(self):
        assert classify_gradient(0.0) == "GREEN"

    def test_gentle_is_green(self):
        assert classify_gradient(5.0) == "GREEN"

    def test_default_amber(self):
        """Default: > 8% → AMBER."""
        assert classify_gradient(9.0) == "AMBER"

    def test_default_red(self):
        """Default: > 12% → RED."""
        assert classify_gradient(13.0) == "RED"

    def test_pantechnicon_stricter_amber(self):
        """Pantechnicon: > 5% → AMBER."""
        assert classify_gradient(6.0, "pantechnicon_18t") == "AMBER"

    def test_pantechnicon_red(self):
        """Pantechnicon: > 8% → RED."""
        assert classify_gradient(9.0, "pantechnicon_18t") == "RED"

    def test_truck_7_5t_amber(self):
        """7.5t truck: > 6% → AMBER."""
        assert classify_gradient(7.0, "truck_7_5t") == "AMBER"

    def test_truck_7_5t_red(self):
        """7.5t truck: > 10% → RED."""
        assert classify_gradient(11.0, "truck_7_5t") == "RED"

    def test_unknown_vehicle_uses_default(self):
        assert classify_gradient(9.0, "unknown_vehicle") == "AMBER"

    def test_boundary_at_amber(self):
        """Exactly at amber threshold → still GREEN (<=)."""
        threshold = GRADIENT_THRESHOLDS["default"]["amber"]
        assert classify_gradient(threshold) == "GREEN"

    def test_boundary_at_red(self):
        """Exactly at red threshold → still AMBER (<=)."""
        threshold = GRADIENT_THRESHOLDS["default"]["red"]
        assert classify_gradient(threshold) == "AMBER"
