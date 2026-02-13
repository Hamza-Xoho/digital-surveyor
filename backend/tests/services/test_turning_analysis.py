"""Tests for turning space analysis."""

import pytest

from app.services.turning_analysis import (
    assess_turning_space,
    compute_max_inscribed_circle_radius,
)
from shapely.geometry import Polygon, mapping


def _make_road_feature(polygon: Polygon) -> dict:
    """Helper to create a GeoJSON feature from a Shapely polygon."""
    return {
        "type": "Feature",
        "geometry": mapping(polygon),
        "properties": {"DescriptiveGroup": "Road Or Track"},
    }


class TestMaxInscribedCircle:
    def test_square(self):
        """10x10 square → inscribed circle radius ≈ 5."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        radius, centre = compute_max_inscribed_circle_radius(poly)
        assert abs(radius - 5.0) < 0.5

    def test_narrow_rectangle(self):
        """2x20 rectangle → inscribed circle radius ≈ 1."""
        poly = Polygon([(0, 0), (20, 0), (20, 2), (0, 2)])
        radius, centre = compute_max_inscribed_circle_radius(poly)
        assert abs(radius - 1.0) < 0.3

    def test_large_circle_area(self):
        """Large polygon → radius > 0."""
        poly = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
        radius, _ = compute_max_inscribed_circle_radius(poly)
        assert radius > 10


class TestAssessTurningSpace:
    def test_large_turning_area_green(self):
        """Large road polygon → GREEN for vehicle with 11m turning radius."""
        road = Polygon([(-30, -30), (30, -30), (30, 30), (-30, 30)])
        features = [_make_road_feature(road)]
        result = assess_turning_space(features, (0, 0), vehicle_turning_radius=11.0)
        assert result["assessed"] is True
        assert result["rating"] == "GREEN"
        assert result["can_turn"] is True

    def test_narrow_road_red(self):
        """Narrow road polygon → RED for vehicle with 11m turning radius."""
        road = Polygon([(-2, -50), (2, -50), (2, 50), (-2, 50)])
        features = [_make_road_feature(road)]
        result = assess_turning_space(features, (0, 0), vehicle_turning_radius=11.0)
        assert result["assessed"] is True
        assert result["rating"] == "RED"
        assert result["can_turn"] is False

    def test_no_road_features_amber(self):
        """No road features → AMBER (can't assess)."""
        result = assess_turning_space([], (0, 0), vehicle_turning_radius=11.0)
        assert result["assessed"] is False
        assert result["rating"] == "AMBER"

    def test_building_features_ignored(self):
        """Building features are not considered for turning."""
        building = {
            "type": "Feature",
            "geometry": mapping(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])),
            "properties": {"DescriptiveGroup": "Building"},
        }
        result = assess_turning_space([building], (0, 0), vehicle_turning_radius=11.0)
        assert result["assessed"] is False

    def test_result_includes_geojson(self):
        road = Polygon([(-30, -30), (30, -30), (30, 30), (-30, 30)])
        features = [_make_road_feature(road)]
        result = assess_turning_space(features, (0, 0), vehicle_turning_radius=11.0)
        assert result["turning_circle_geojson"] is not None
        assert result["turning_circle_geojson"]["type"] == "Feature"
