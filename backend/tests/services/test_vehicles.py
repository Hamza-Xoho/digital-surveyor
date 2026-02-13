"""Tests for vehicle profile service."""

import pytest

from app.services.vehicles import get_vehicles, load_all_vehicles


class TestLoadAllVehicles:
    def test_returns_tuple(self):
        result = load_all_vehicles()
        assert isinstance(result, tuple)

    def test_not_empty(self):
        result = load_all_vehicles()
        assert len(result) > 0

    def test_vehicle_has_required_fields(self):
        vehicles = load_all_vehicles()
        required = {"name", "vehicle_class", "width_m", "height_m", "weight_kg", "turning_radius_m"}
        for v in vehicles:
            assert required.issubset(v.keys()), f"Vehicle missing fields: {required - set(v.keys())}"


class TestGetVehicles:
    def test_all_vehicles(self):
        all_v = get_vehicles()
        assert len(all_v) == len(load_all_vehicles())

    def test_filter_by_class(self):
        all_v = get_vehicles()
        if all_v:
            first_class = all_v[0]["vehicle_class"]
            filtered = get_vehicles([first_class])
            assert len(filtered) == 1
            assert filtered[0]["vehicle_class"] == first_class

    def test_filter_nonexistent_class(self):
        result = get_vehicles(["nonexistent_vehicle_class"])
        assert result == []

    def test_filter_multiple_classes(self):
        all_v = get_vehicles()
        if len(all_v) >= 2:
            classes = [all_v[0]["vehicle_class"], all_v[1]["vehicle_class"]]
            filtered = get_vehicles(classes)
            assert len(filtered) == 2
