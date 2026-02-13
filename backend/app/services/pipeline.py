import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.services.geocoding import geocode_postcode
from app.services.here_routing import check_truck_restrictions
from app.services.lidar import find_lidar_tile, get_gradient_profile
from app.services.os_features import fetch_area_features, fetch_line_features, get_features_wgs84
from app.services.scoring import score_vehicle_access
from app.services.turning_analysis import assess_turning_space
from app.services.vehicles import get_vehicles
from app.services.width_analysis import compute_road_widths

logger = logging.getLogger(__name__)


async def run_full_assessment(
    postcode: str,
    vehicle_classes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Full assessment pipeline: postcode → Green/Amber/Red for each vehicle.

    Steps:
    1. Geocode postcode
    2. Fetch OS features (parallel: areas + lines)
    3. Get LiDAR gradient (if tile available)
    4. Compute road widths
    5. Assess turning space (if dead-end detected)
    6. Check route restrictions via HERE (per vehicle)
    7. Score each vehicle

    Returns complete assessment with data for frontend display.
    """
    # Step 1: Geocode
    coords = await geocode_postcode(postcode)
    easting = coords["easting"]
    northing = coords["northing"]
    lat = coords["latitude"]
    lon = coords["longitude"]

    # Step 2: Fetch OS features (parallel)
    area_features, line_features = await asyncio.gather(
        fetch_area_features(easting, northing),
        fetch_line_features(easting, northing),
    )

    # Step 3: LiDAR gradient
    gradient_result = None
    tile_path = find_lidar_tile(easting, northing, settings.LIDAR_TILES_PATH)
    if tile_path:
        try:
            # Simple straight-line approach path (property to 100m away on road)
            approach_path = [
                (easting, northing),
                (easting, northing + 100),  # Simplified: straight north
            ]
            gradient_result = get_gradient_profile(approach_path, tile_path)
        except Exception as e:
            logger.warning("Gradient analysis failed: %s", e)
    else:
        logger.info("No LiDAR tile for (%s, %s) — skipping gradient", easting, northing)

    # Step 4: Compute road widths
    width_result = compute_road_widths(line_features)

    # Step 5: Assess turning (simplified — always run, let it determine if dead-end)
    vehicles = get_vehicles(vehicle_classes)
    turning_results = {}
    for v in vehicles:
        try:
            turning = assess_turning_space(
                area_features.get("features", []),
                (easting, northing),
                v["turning_radius_m"],
            )
            turning_results[v["vehicle_class"]] = turning
        except Exception as e:
            logger.warning("Turning analysis failed for %s: %s", v["name"], e)
            turning_results[v["vehicle_class"]] = None

    # Step 6: Route restrictions (parallel per vehicle)
    route_results = {}
    if settings.HERE_API_KEY:
        # Use a reference point ~1km away as origin
        origin = (lat + 0.009, lon)  # Approx 1km north
        restriction_tasks = []
        for v in vehicles:
            task = check_truck_restrictions(
                origin=origin,
                destination=(lat, lon),
                vehicle_height_m=v["height_m"],
                vehicle_width_m=v["width_m"],
                vehicle_weight_kg=v["weight_kg"],
            )
            restriction_tasks.append((v["vehicle_class"], task))

        results = await asyncio.gather(
            *[t for _, t in restriction_tasks],
            return_exceptions=True,
        )
        for i, (vc, _) in enumerate(restriction_tasks):
            if isinstance(results[i], Exception):
                logger.warning("HERE routing failed for %s: %s", vc, results[i])
                route_results[vc] = None
            else:
                route_results[vc] = results[i]

    # Step 7: Score each vehicle
    vehicle_assessments = []
    for v in vehicles:
        score = score_vehicle_access(
            vehicle=v,
            width_result=width_result,
            gradient_result=gradient_result,
            turning_result=turning_results.get(v["vehicle_class"]),
            route_restrictions=route_results.get(v["vehicle_class"]),
        )
        vehicle_assessments.append(score)

    # Determine overall rating
    all_ratings = [va["overall_rating"] for va in vehicle_assessments]
    if "RED" in all_ratings:
        overall = "RED"
    elif "AMBER" in all_ratings:
        overall = "AMBER"
    else:
        overall = "GREEN"

    # Build GeoJSON overlays for frontend
    area_wgs84 = get_features_wgs84(area_features)
    line_wgs84 = get_features_wgs84(line_features)
    width_lines_wgs84 = get_features_wgs84(
        width_result.get("measurement_lines_geojson", {"type": "FeatureCollection", "features": []})
    )

    # Filter buildings from area features
    buildings = {
        "type": "FeatureCollection",
        "features": [
            f for f in area_wgs84.get("features", [])
            if f.get("properties", {}).get("DescriptiveGroup") == "Building"
        ],
    }

    roads = {
        "type": "FeatureCollection",
        "features": [
            f for f in area_wgs84.get("features", [])
            if f.get("properties", {}).get("DescriptiveGroup") == "Road Or Track"
        ],
    }

    return {
        "postcode": coords["postcode"],
        "latitude": lat,
        "longitude": lon,
        "easting": easting,
        "northing": northing,
        "overall_rating": overall,
        "vehicle_assessments": vehicle_assessments,
        "width_analysis": {
            "min_width_m": width_result["min_width_m"],
            "max_width_m": width_result["max_width_m"],
            "mean_width_m": width_result["mean_width_m"],
            "pinch_points": width_result.get("pinch_points", []),
        },
        "gradient_analysis": (
            {
                "max_gradient_pct": gradient_result["max_gradient_pct"],
                "mean_gradient_pct": gradient_result["mean_gradient_pct"],
                "steep_segments": gradient_result.get("steep_segments", []),
            }
            if gradient_result
            else None
        ),
        "geojson_overlays": {
            "roads": roads,
            "buildings": buildings,
            "width_measurements": width_lines_wgs84,
            "gradient_profile": (
                gradient_result.get("profile_geojson") if gradient_result else None
            ),
        },
    }
