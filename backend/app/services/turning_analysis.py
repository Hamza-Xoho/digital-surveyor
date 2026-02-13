import logging
from typing import Any

from shapely.geometry import shape, Point, Polygon, mapping
from shapely.ops import unary_union

logger = logging.getLogger(__name__)


def compute_max_inscribed_circle_radius(polygon: Polygon) -> tuple[float, Point]:
    """
    Approximate the maximum inscribed circle radius of a polygon.
    Uses iterative point sampling to find the point furthest from any edge.
    """
    bounds = polygon.bounds
    best_radius = 0.0
    best_centre = polygon.centroid

    # Sample grid within bounding box
    n_samples = 20
    for i in range(n_samples):
        for j in range(n_samples):
            x = bounds[0] + (bounds[2] - bounds[0]) * (i + 0.5) / n_samples
            y = bounds[1] + (bounds[3] - bounds[1]) * (j + 0.5) / n_samples
            pt = Point(x, y)
            if polygon.contains(pt):
                dist = polygon.boundary.distance(pt)
                if dist > best_radius:
                    best_radius = dist
                    best_centre = pt

    return round(best_radius, 2), best_centre


def assess_turning_space(
    road_area_features: list[dict],
    junction_point: tuple[float, float],
    vehicle_turning_radius: float,
    search_radius: float = 30.0,
) -> dict[str, Any]:
    """
    At dead-ends, check if there is enough space to turn the vehicle.

    1. Find road area polygons near the junction point.
    2. Merge them into a single turning area polygon.
    3. Compute max inscribed circle.
    4. Compare against vehicle turning radius.
    """
    junction_pt = Point(junction_point)

    # Find road polygons near the junction
    nearby_road_polys = []
    for f in road_area_features:
        group = f.get("properties", {}).get("DescriptiveGroup", "")
        if "Road" not in group and "Track" not in group:
            continue
        try:
            geom = shape(f["geometry"])
            if geom.distance(junction_pt) <= search_radius:
                nearby_road_polys.append(geom)
        except Exception:
            continue

    if not nearby_road_polys:
        return {
            "assessed": False,
            "is_dead_end": False,
            "available_radius_m": 0,
            "required_radius_m": vehicle_turning_radius,
            "can_turn": True,  # Assume OK if we can't assess
            "rating": "AMBER",
            "detail": "No road polygons found near junction — cannot assess turning",
            "turning_circle_geojson": None,
        }

    # Merge nearby road polygons into one turning area
    merged = unary_union(nearby_road_polys)
    if merged.geom_type == "MultiPolygon":
        # Use the largest polygon
        merged = max(merged.geoms, key=lambda g: g.area)

    # Compute max inscribed circle
    radius, centre = compute_max_inscribed_circle_radius(merged)

    can_turn = radius >= vehicle_turning_radius
    rating = "GREEN" if can_turn else "RED"

    # Build turning circle GeoJSON for map display
    turning_circle = centre.buffer(vehicle_turning_radius)

    return {
        "assessed": True,
        "is_dead_end": True,
        "available_radius_m": radius,
        "required_radius_m": vehicle_turning_radius,
        "can_turn": can_turn,
        "rating": rating,
        "detail": (
            f"Available: {radius}m radius, Required: {vehicle_turning_radius}m — "
            f"{'sufficient' if can_turn else 'INSUFFICIENT'}"
        ),
        "turning_circle_geojson": {
            "type": "Feature",
            "geometry": mapping(turning_circle),
            "properties": {
                "radius_m": vehicle_turning_radius,
                "available_radius_m": radius,
                "can_turn": can_turn,
            },
        },
    }
