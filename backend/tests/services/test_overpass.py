"""Tests for the Overpass API fallback service."""

import pytest

from app.services.overpass import (
    OSM_ROAD_WIDTH_ESTIMATES,
    _build_overpass_query,
    _osm_to_bng_geojson,
    compute_road_widths_from_osm,
)


class TestBuildOverpassQuery:
    def test_query_contains_coordinates(self):
        query = _build_overpass_query(51.5, -0.1, radius=200)
        assert "51.5" in query
        assert "-0.1" in query
        assert "200" in query
        assert "[out:json]" in query

    def test_query_filters_highways(self):
        query = _build_overpass_query(51.5, -0.1)
        assert '"highway"' in query


class TestOsmRoadWidthEstimates:
    def test_residential_width(self):
        assert OSM_ROAD_WIDTH_ESTIMATES["residential"] == 5.5

    def test_motorway_wider_than_residential(self):
        assert OSM_ROAD_WIDTH_ESTIMATES["motorway"] > OSM_ROAD_WIDTH_ESTIMATES["residential"]

    def test_service_narrower_than_primary(self):
        assert OSM_ROAD_WIDTH_ESTIMATES["service"] < OSM_ROAD_WIDTH_ESTIMATES["primary"]


class TestOsmToBngGeojson:
    def test_empty_elements(self):
        result = _osm_to_bng_geojson([], {})
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []
        assert result["source"] == "overpass_api"

    def test_way_with_nodes(self):
        nodes = {
            1: (-0.1, 51.5),
            2: (-0.101, 51.501),
        }
        elements = [
            {
                "type": "way",
                "tags": {"highway": "residential", "name": "Test Road"},
                "nodes": [1, 2],
            }
        ]
        result = _osm_to_bng_geojson(elements, nodes)
        assert len(result["features"]) == 1
        feature = result["features"][0]
        assert feature["properties"]["highway"] == "residential"
        assert feature["properties"]["name"] == "Test Road"
        assert feature["properties"]["width_m"] == 5.5
        assert feature["properties"]["source"] == "osm"
        assert feature["geometry"]["type"] == "LineString"
        assert len(feature["geometry"]["coordinates"]) == 2

    def test_way_with_explicit_width_tag(self):
        nodes = {1: (-0.1, 51.5), 2: (-0.101, 51.501)}
        elements = [
            {
                "type": "way",
                "tags": {"highway": "residential", "width": "7.5m"},
                "nodes": [1, 2],
            }
        ]
        result = _osm_to_bng_geojson(elements, nodes)
        assert result["features"][0]["properties"]["width_m"] == 7.5

    def test_skips_non_way_elements(self):
        elements = [{"type": "node", "id": 1}]
        result = _osm_to_bng_geojson(elements, {})
        assert result["features"] == []

    def test_skips_ways_without_highway(self):
        nodes = {1: (-0.1, 51.5), 2: (-0.101, 51.501)}
        elements = [
            {"type": "way", "tags": {"building": "yes"}, "nodes": [1, 2]}
        ]
        result = _osm_to_bng_geojson(elements, nodes)
        assert result["features"] == []


class TestComputeRoadWidthsFromOsm:
    def test_empty_features(self):
        result = compute_road_widths_from_osm({"features": []})
        assert result["sample_count"] == 0
        assert result["source"] == "osm"

    def test_single_road(self):
        features = {
            "features": [
                {
                    "properties": {"highway": "residential", "width_m": 5.5, "name": "Test Rd"},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
                }
            ]
        }
        result = compute_road_widths_from_osm(features)
        assert result["min_width_m"] == 5.5
        assert result["max_width_m"] == 5.5
        assert result["mean_width_m"] == 5.5
        assert result["sample_count"] == 1

    def test_mixed_road_types(self):
        features = {
            "features": [
                {
                    "properties": {"highway": "residential", "width_m": 5.5},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
                },
                {
                    "properties": {"highway": "service", "width_m": 3.7},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
                },
            ]
        }
        result = compute_road_widths_from_osm(features)
        assert result["min_width_m"] == 3.7
        assert result["max_width_m"] == 5.5
        assert result["sample_count"] == 2

    def test_footway_excluded_when_vehicle_roads_present(self):
        features = {
            "features": [
                {
                    "properties": {"highway": "residential", "width_m": 5.5},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
                },
                {
                    "properties": {"highway": "footway", "width_m": 1.5},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
                },
            ]
        }
        result = compute_road_widths_from_osm(features)
        # Footway should be excluded since we have a vehicle road
        assert result["min_width_m"] == 5.5
        assert result["sample_count"] == 1
