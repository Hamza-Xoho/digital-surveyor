"""Road width analysis — computes actual road widths from OS MasterMap edge lines.

This is the core computation of the Digital Surveyor. Given opposing kerb-edge
line features from OS MasterMap TopographicLine data, it computes perpendicular
distances between them to determine the road width at multiple sample points.

Uses Shapely for all geometry operations. All coordinates are in
British National Grid (EPSG:27700) metres.
"""

import math
import statistics
from typing import Any

from shapely.geometry import LineString, Point, mapping


def _line_bearing(line: LineString) -> float:
    """Compute overall bearing of a linestring in degrees (0-180, undirected)."""
    coords = list(line.coords)
    if len(coords) < 2:
        return 0.0
    dx = coords[-1][0] - coords[0][0]
    dy = coords[-1][1] - coords[0][1]
    bearing = math.degrees(math.atan2(dx, dy)) % 360
    # Normalise to 0-180 (undirected)
    if bearing > 180:
        bearing -= 180
    return bearing


def _bearing_diff(b1: float, b2: float) -> float:
    """Angular difference between two bearings (0-90 range)."""
    diff = abs(b1 - b2) % 180
    if diff > 90:
        diff = 180 - diff
    return diff


def find_opposing_edge_pairs(
    line_features: list[dict[str, Any]],
    bearing_tolerance: float = 15.0,
    min_distance: float = 2.0,
    max_distance: float = 15.0,
) -> list[tuple[LineString, LineString]]:
    """
    Find pairs of lines that represent opposing kerb edges of the same road.

    Logic:
    1. Convert GeoJSON features to Shapely LineStrings.
    2. Compute bearing for each line.
    3. Find pairs with similar bearing (within tolerance), roughly parallel,
       and separated by 2-15m (typical UK road width range).

    Returns list of (left_edge, right_edge) tuples.
    """
    lines_with_bearing: list[tuple[LineString, float]] = []

    for feature in line_features:
        geom = feature.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        line = LineString(coords)
        if line.length < 3.0:  # Skip very short segments
            continue
        bearing = _line_bearing(line)
        lines_with_bearing.append((line, bearing))

    pairs: list[tuple[LineString, LineString]] = []
    used: set[int] = set()

    for i, (line_a, bearing_a) in enumerate(lines_with_bearing):
        if i in used:
            continue
        best_match: int | None = None
        best_dist = float("inf")

        for j, (line_b, bearing_b) in enumerate(lines_with_bearing):
            if j <= i or j in used:
                continue

            # Check bearings are roughly parallel
            if _bearing_diff(bearing_a, bearing_b) > bearing_tolerance:
                continue

            # Check distance between midpoints
            mid_a = line_a.interpolate(0.5, normalized=True)
            mid_b = line_b.interpolate(0.5, normalized=True)
            dist = mid_a.distance(mid_b)

            if min_distance <= dist <= max_distance and dist < best_dist:
                best_dist = dist
                best_match = j

        if best_match is not None:
            pairs.append((lines_with_bearing[i][0], lines_with_bearing[best_match][0]))
            used.add(i)
            used.add(best_match)

    return pairs


def sample_perpendicular_widths(
    edge_left: LineString,
    edge_right: LineString,
    n_samples: int = 20,
) -> list[dict[str, Any]]:
    """
    Sample perpendicular distances between two opposing road edges.

    For each sample point on edge_left:
    1. Interpolate a point at regular intervals.
    2. Find nearest point on edge_right.
    3. Compute distance = road width at that point.

    Returns list of measurement dicts.
    """
    widths: list[dict[str, Any]] = []

    for i in range(n_samples):
        frac = i / max(n_samples - 1, 1)
        pt_left = edge_left.interpolate(frac, normalized=True)

        # Find nearest point on right edge
        nearest_dist_along = edge_right.project(pt_left)
        pt_right = edge_right.interpolate(nearest_dist_along)

        width = pt_left.distance(pt_right)

        widths.append({
            "fraction": round(frac, 3),
            "width_m": round(width, 2),
            "left_point": [pt_left.x, pt_left.y],
            "right_point": [pt_right.x, pt_right.y],
        })

    return widths


def _measurements_to_geojson(measurements: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert width measurements to GeoJSON lines for map display."""
    features = []
    for m in measurements:
        line = LineString([m["left_point"], m["right_point"]])
        features.append({
            "type": "Feature",
            "geometry": mapping(line),
            "properties": {
                "width_m": m["width_m"],
                "fraction": m["fraction"],
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def compute_road_widths(line_features_geojson: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point — compute road widths from OS MasterMap line features.

    Args:
        line_features_geojson: GeoJSON FeatureCollection of TopographicLine features

    Returns:
        {
            "min_width_m": 3.2,
            "max_width_m": 5.1,
            "mean_width_m": 4.1,
            "sample_count": 40,
            "pinch_points": [{"location": [e, n], "width_m": 3.2}],
            "measurements": [...],
            "measurement_lines_geojson": {...},
        }
    """
    features = line_features_geojson.get("features", [])

    if not features:
        return {
            "min_width_m": 0.0,
            "max_width_m": 0.0,
            "mean_width_m": 0.0,
            "sample_count": 0,
            "pinch_points": [],
            "measurements": [],
            "measurement_lines_geojson": {"type": "FeatureCollection", "features": []},
            "error": "No line features available for width computation",
        }

    pairs = find_opposing_edge_pairs(features)

    if not pairs:
        return {
            "min_width_m": 0.0,
            "max_width_m": 0.0,
            "mean_width_m": 0.0,
            "sample_count": 0,
            "pinch_points": [],
            "measurements": [],
            "measurement_lines_geojson": {"type": "FeatureCollection", "features": []},
            "error": "Could not find opposing road edge pairs",
        }

    all_measurements: list[dict[str, Any]] = []
    for left, right in pairs:
        samples = sample_perpendicular_widths(left, right)
        all_measurements.extend(samples)

    if not all_measurements:
        return {
            "min_width_m": 0.0,
            "max_width_m": 0.0,
            "mean_width_m": 0.0,
            "sample_count": 0,
            "pinch_points": [],
            "measurements": [],
            "measurement_lines_geojson": {"type": "FeatureCollection", "features": []},
            "error": "No width measurements from edge pairs",
        }

    width_values = [m["width_m"] for m in all_measurements]
    min_w = min(width_values)
    max_w = max(width_values)
    mean_w = statistics.mean(width_values)

    # Find pinch points (narrowest 10% of measurements)
    threshold = sorted(width_values)[max(1, len(width_values) // 10) - 1]
    pinch_points = [
        {"location": m["left_point"], "width_m": m["width_m"]}
        for m in all_measurements
        if m["width_m"] <= threshold
    ]

    return {
        "min_width_m": round(min_w, 2),
        "max_width_m": round(max_w, 2),
        "mean_width_m": round(mean_w, 2),
        "sample_count": len(all_measurements),
        "pinch_points": pinch_points,
        "measurements": all_measurements,
        "measurement_lines_geojson": _measurements_to_geojson(all_measurements),
    }


def check_vehicle_width_fit(
    road_min_width: float,
    vehicle_width: float,
    mirror_width: float = 0.25,
    clearance_margin: float = 0.5,
) -> dict[str, Any]:
    """
    Check if a vehicle fits on the road.

    Returns:
        {
            "fits": True/False,
            "total_vehicle_width_m": 2.75,
            "required_width_m": 3.25,
            "available_width_m": 3.8,
            "clearance_m": 0.55,
            "rating": "GREEN" / "AMBER" / "RED",
        }

    Thresholds:
        clearance > 0.5m   → GREEN
        clearance 0-0.5m   → AMBER
        clearance < 0       → RED (doesn't fit)
    """
    total_vehicle = vehicle_width + (2 * mirror_width)
    clearance = road_min_width - total_vehicle

    if clearance >= clearance_margin:
        rating = "GREEN"
    elif clearance >= 0:
        rating = "AMBER"
    else:
        rating = "RED"

    return {
        "fits": clearance >= 0,
        "total_vehicle_width_m": round(total_vehicle, 2),
        "required_width_m": round(total_vehicle + clearance_margin, 2),
        "available_width_m": round(road_min_width, 2),
        "clearance_m": round(clearance, 2),
        "rating": rating,
    }
