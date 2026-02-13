"""Tests for scoring service — vehicle access rating aggregation."""

import pytest

from app.services.scoring import score_vehicle_access


SAMPLE_VEHICLE = {
    "name": "18t Pantechnicon",
    "vehicle_class": "pantechnicon_18t",
    "width_m": 2.55,
    "height_m": 4.0,
    "weight_kg": 18000,
    "turning_radius_m": 11.0,
    "mirror_width_m": 0.25,
}


class TestScoreVehicleAccess:
    def test_all_green(self):
        """All checks pass → overall GREEN."""
        width = {"min_width_m": 5.0, "max_width_m": 6.0, "mean_width_m": 5.5}
        gradient = {"max_gradient_pct": 2.0, "mean_gradient_pct": 1.0}
        turning = {"assessed": True, "rating": "GREEN", "detail": "OK", "available_radius_m": 15, "required_radius_m": 11}
        route = {"rating": "GREEN", "warnings": [], "restrictions": []}

        result = score_vehicle_access(SAMPLE_VEHICLE, width, gradient, turning, route)
        assert result["overall_rating"] == "GREEN"
        assert result["confidence"] == 1.0
        assert len(result["checks"]) == 4

    def test_red_width_dominates(self):
        """RED width check → overall RED."""
        width = {"min_width_m": 2.5, "max_width_m": 3.0, "mean_width_m": 2.7}
        gradient = {"max_gradient_pct": 2.0, "mean_gradient_pct": 1.0}
        turning = {"assessed": True, "rating": "GREEN", "detail": "OK", "available_radius_m": 15, "required_radius_m": 11}
        route = {"rating": "GREEN", "warnings": [], "restrictions": []}

        result = score_vehicle_access(SAMPLE_VEHICLE, width, gradient, turning, route)
        assert result["overall_rating"] == "RED"

    def test_missing_data_gives_amber(self):
        """No data → all checks AMBER → overall AMBER."""
        result = score_vehicle_access(SAMPLE_VEHICLE, None, None, None, None)
        assert result["overall_rating"] == "AMBER"
        assert result["confidence"] < 1.0

    def test_confidence_partial_data(self):
        """Only width data → 50% confidence (width + turning default counts)."""
        width = {"min_width_m": 5.0, "max_width_m": 6.0, "mean_width_m": 5.5}
        result = score_vehicle_access(SAMPLE_VEHICLE, width, None, None, None)
        assert 0.0 < result["confidence"] < 1.0

    def test_recommendation_green(self):
        width = {"min_width_m": 5.0, "max_width_m": 6.0, "mean_width_m": 5.5}
        gradient = {"max_gradient_pct": 2.0, "mean_gradient_pct": 1.0}
        turning = {"assessed": True, "rating": "GREEN", "detail": "OK", "available_radius_m": 15, "required_radius_m": 11}
        route = {"rating": "GREEN", "warnings": [], "restrictions": []}

        result = score_vehicle_access(SAMPLE_VEHICLE, width, gradient, turning, route)
        assert "clear" in result["recommendation"].lower() or "passed" in result["recommendation"].lower()

    def test_recommendation_red(self):
        width = {"min_width_m": 2.0}
        result = score_vehicle_access(SAMPLE_VEHICLE, width, None, None, None)
        assert "cannot" in result["recommendation"].lower() or "failed" in result["recommendation"].lower()

    def test_vehicle_info_in_result(self):
        result = score_vehicle_access(SAMPLE_VEHICLE, None, None, None, None)
        assert result["vehicle_name"] == SAMPLE_VEHICLE["name"]
        assert result["vehicle_class"] == SAMPLE_VEHICLE["vehicle_class"]

    def test_turning_not_assessed_is_green(self):
        """If turning couldn't be assessed (not dead-end), it defaults to GREEN."""
        turning = {"assessed": False}
        result = score_vehicle_access(SAMPLE_VEHICLE, None, None, turning, None)
        turning_check = [c for c in result["checks"] if c["name"] == "Turning Space"][0]
        assert turning_check["rating"] == "GREEN"
