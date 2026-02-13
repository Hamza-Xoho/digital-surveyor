"""Tests for road width analysis — perpendicular widths, vehicle fit, edge pairing."""

import pytest
from shapely.geometry import LineString, mapping

from app.services.width_analysis import (
    check_vehicle_width_fit,
    compute_road_widths,
    find_opposing_edge_pairs,
    sample_perpendicular_widths,
)


def _make_line_feature(line: LineString, group: str = "Road Or Track") -> dict:
    """Helper to create a GeoJSON feature from a Shapely LineString."""
    return {
        "type": "Feature",
        "geometry": mapping(line),
        "properties": {"DescriptiveGroup": group},
    }


class TestPerpendicularWidths:
    def test_parallel_lines_4m(self):
        """Two parallel lines 4.0m apart → mean width ≈ 4.0."""
        left = LineString([(0, 0), (50, 0)])
        right = LineString([(0, 4), (50, 4)])
        widths = sample_perpendicular_widths(left, right, n_samples=10)
        mean = sum(w["width_m"] for w in widths) / len(widths)
        assert abs(mean - 4.0) < 0.1, f"Expected ~4.0, got {mean}"

    def test_converging_lines(self):
        """Lines narrowing from 5m to 3m → min ≈ 3.0."""
        left = LineString([(0, 0), (50, 0)])
        right = LineString([(0, 5), (50, 3)])
        widths = sample_perpendicular_widths(left, right, n_samples=20)
        min_w = min(w["width_m"] for w in widths)
        assert abs(min_w - 3.0) < 0.3, f"Expected min ~3.0, got {min_w}"

    def test_sample_count(self):
        left = LineString([(0, 0), (50, 0)])
        right = LineString([(0, 4), (50, 4)])
        widths = sample_perpendicular_widths(left, right, n_samples=15)
        assert len(widths) == 15

    def test_measurement_structure(self):
        left = LineString([(0, 0), (50, 0)])
        right = LineString([(0, 4), (50, 4)])
        widths = sample_perpendicular_widths(left, right, n_samples=5)
        for w in widths:
            assert "width_m" in w
            assert "fraction" in w
            assert "left_point" in w
            assert "right_point" in w


class TestVehicleFit:
    def test_green_wide_road(self):
        """4.0m road, 2.55m vehicle → GREEN (0.7m clearance)."""
        result = check_vehicle_width_fit(4.0, 2.55, 0.25, 0.5)
        assert result["rating"] == "GREEN"
        assert result["fits"] is True
        assert result["clearance_m"] > 0.5

    def test_amber_tight_road(self):
        """3.3m road, 2.55m vehicle → AMBER (0.25m clearance)."""
        result = check_vehicle_width_fit(3.3, 2.55, 0.25, 0.5)
        assert result["rating"] == "AMBER"
        assert result["fits"] is True
        assert 0 <= result["clearance_m"] < 0.5

    def test_red_too_narrow(self):
        """2.8m road, 2.55m vehicle → RED (negative clearance)."""
        result = check_vehicle_width_fit(2.8, 2.55, 0.25, 0.5)
        assert result["rating"] == "RED"
        assert result["fits"] is False
        assert result["clearance_m"] < 0

    def test_luton_van_fit(self):
        """3.5m road, 2.25m van → GREEN."""
        result = check_vehicle_width_fit(3.5, 2.25, 0.25, 0.5)
        assert result["rating"] == "GREEN"

    def test_exact_fit(self):
        """3.05m road, 2.55m vehicle + 0.5m mirrors → clearance 0, AMBER."""
        result = check_vehicle_width_fit(3.05, 2.55, 0.25, 0.5)
        assert result["rating"] == "AMBER"
        assert abs(result["clearance_m"]) < 0.01


class TestFindOpposingEdgePairs:
    def test_parallel_edges(self):
        """Two parallel lines 5m apart → found as a pair."""
        features = [
            _make_line_feature(LineString([(0, 0), (50, 0)])),
            _make_line_feature(LineString([(0, 5), (50, 5)])),
        ]
        pairs = find_opposing_edge_pairs(features)
        assert len(pairs) == 1

    def test_perpendicular_not_paired(self):
        """Perpendicular lines → NOT paired."""
        features = [
            _make_line_feature(LineString([(0, 0), (50, 0)])),
            _make_line_feature(LineString([(25, -20), (25, 20)])),
        ]
        pairs = find_opposing_edge_pairs(features)
        assert len(pairs) == 0

    def test_too_far_apart(self):
        """Lines 20m apart → NOT paired (max is 15m)."""
        features = [
            _make_line_feature(LineString([(0, 0), (50, 0)])),
            _make_line_feature(LineString([(0, 20), (50, 20)])),
        ]
        pairs = find_opposing_edge_pairs(features)
        assert len(pairs) == 0


class TestComputeRoadWidths:
    def test_empty_features(self):
        result = compute_road_widths({"type": "FeatureCollection", "features": []})
        assert result["min_width_m"] == 0.0
        assert result["sample_count"] == 0

    def test_with_parallel_edges(self):
        features = [
            _make_line_feature(LineString([(0, 0), (50, 0)])),
            _make_line_feature(LineString([(0, 5), (50, 5)])),
        ]
        result = compute_road_widths({"type": "FeatureCollection", "features": features})
        assert result["min_width_m"] > 0
        assert result["mean_width_m"] > 0
        assert result["sample_count"] > 0
        assert "measurement_lines_geojson" in result
