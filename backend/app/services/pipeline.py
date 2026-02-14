import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.services.geocoding import geocode_postcode
from app.services.here_routing import check_truck_restrictions
from app.services.lidar import find_lidar_tile, get_gradient_profile
from app.services.open_elevation import get_gradient_profile_from_api
from app.services.os_features import fetch_area_features, fetch_line_features, get_features_wgs84
from app.services.overpass import (
    compute_road_widths_from_osm,
    fetch_osm_building_features,
    fetch_osm_road_features,
)
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
    2. Fetch road/building features (OS MasterMap → Overpass API fallback)
    3. Get gradient profile (LiDAR → Open Elevation API fallback)
    4. Compute road widths
    5. Assess turning space (if dead-end detected)
    6. Check route restrictions via HERE (per vehicle)
    7. Score each vehicle

    Returns complete assessment with data for frontend display.
    """
    # Track data sources used through the pipeline
    data_sources: dict[str, dict[str, Any]] = {}

    # Step 1: Geocode
    coords = await geocode_postcode(postcode)
    easting = coords["easting"]
    northing = coords["northing"]
    lat = coords["latitude"]
    lon = coords["longitude"]
    data_sources["geocoding"] = {"source": "postcodes.io", "status": "ok"}

    # Step 2: Fetch features (OS MasterMap with Overpass fallback)
    area_features, line_features, road_source = await _fetch_features_with_fallback(
        easting, northing, lat, lon
    )
    data_sources["road_geometry"] = road_source

    # Step 3: Gradient profile (LiDAR with elevation API fallback)
    gradient_result, gradient_source = await _get_gradient_with_fallback(
        easting, northing, lat, lon
    )
    data_sources["elevation"] = gradient_source

    # Step 4: Compute road widths
    if line_features.get("source") == "overpass_api":
        width_result = compute_road_widths_from_osm(line_features)
        data_sources["width_analysis"] = {
            "source": "osm_estimates",
            "status": "ok",
            "note": "Widths estimated from road classification",
        }
    else:
        width_result = compute_road_widths(line_features)
        if width_result.get("error"):
            data_sources["width_analysis"] = {
                "source": "os_mastermap",
                "status": "degraded",
                "note": width_result["error"],
            }
        else:
            data_sources["width_analysis"] = {
                "source": "os_mastermap",
                "status": "ok",
            }

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

        data_sources["route_restrictions"] = {"source": "here_api", "status": "ok"}
    else:
        data_sources["route_restrictions"] = {
            "source": "none",
            "status": "unavailable",
            "note": "HERE_API_KEY not configured",
        }

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
    if line_features.get("source") == "overpass_api":
        line_wgs84 = _osm_features_to_wgs84(line_features)
        area_wgs84 = _osm_features_to_wgs84(area_features)
    else:
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
        "data_sources": data_sources,
        "geojson_overlays": {
            "roads": roads,
            "buildings": buildings,
            "road_lines": line_wgs84,
            "width_measurements": width_lines_wgs84,
            "gradient_profile": (
                gradient_result.get("profile_geojson") if gradient_result else None
            ),
        },
    }


async def _fetch_features_with_fallback(
    easting: float,
    northing: float,
    lat: float,
    lon: float,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Fetch road/building features with OS → Overpass fallback.

    Returns:
        (area_features, line_features, data_source_info)
    """
    if settings.OS_API_KEY:
        area_features, line_features = await asyncio.gather(
            fetch_area_features(easting, northing),
            fetch_line_features(easting, northing),
        )

        has_areas = len(area_features.get("features", [])) > 0
        has_lines = len(line_features.get("features", [])) > 0

        if has_areas or has_lines:
            source_info = {"source": "os_mastermap", "status": "ok"}
            return area_features, line_features, source_info

        logger.info("OS API returned empty results, falling back to Overpass")

    # Fallback to Overpass API (free, no key)
    logger.info("Using Overpass API for road/building data")
    line_features, area_features = await asyncio.gather(
        fetch_osm_road_features(lat, lon),
        fetch_osm_building_features(lat, lon),
    )

    has_features = (
        len(line_features.get("features", [])) > 0
        or len(area_features.get("features", [])) > 0
    )

    if has_features:
        source_info = {
            "source": "openstreetmap",
            "status": "ok",
            "note": "Using free OpenStreetMap data via Overpass API",
        }
    else:
        source_info = {
            "source": "openstreetmap",
            "status": "degraded",
            "note": "Overpass API returned no features for this area",
        }

    return area_features, line_features, source_info


async def _get_gradient_with_fallback(
    easting: float,
    northing: float,
    lat: float,
    lon: float,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Get gradient profile with LiDAR → elevation API fallback.

    Returns:
        (gradient_result, data_source_info)
    """
    tile_path = find_lidar_tile(easting, northing, settings.LIDAR_TILES_PATH)
    if tile_path:
        try:
            approach_path = [
                (easting, northing),
                (easting, northing + 100),
            ]
            gradient_result = get_gradient_profile(approach_path, tile_path)
            source_info = {
                "source": "lidar_dtm",
                "status": "ok",
                "resolution": "1m",
            }
            return gradient_result, source_info
        except Exception as e:
            logger.warning("LiDAR gradient analysis failed: %s", e)

    # Fallback to elevation API
    logger.info("No LiDAR tile, using elevation API fallback")
    try:
        approach_path_wgs84 = [
            (lat, lon),
            (lat + 0.0009, lon),  # ~100m north
        ]
        # Add intermediate points for better resolution
        n_points = 10
        points = []
        for i in range(n_points + 1):
            frac = i / n_points
            p_lat = approach_path_wgs84[0][0] + frac * (approach_path_wgs84[1][0] - approach_path_wgs84[0][0])
            p_lon = approach_path_wgs84[0][1] + frac * (approach_path_wgs84[1][1] - approach_path_wgs84[0][1])
            points.append((p_lat, p_lon))

        gradient_result = await get_gradient_profile_from_api(points)

        if gradient_result.get("error"):
            source_info = {
                "source": "elevation_api",
                "status": "degraded",
                "note": gradient_result["error"],
            }
            return None, source_info

        source_info = {
            "source": "elevation_api",
            "status": "ok",
            "resolution": "~30m (SRTM)",
            "note": "Using free elevation API (lower resolution than LiDAR)",
        }
        return gradient_result, source_info

    except Exception as e:
        logger.warning("Elevation API fallback failed: %s", e)
        source_info = {
            "source": "none",
            "status": "unavailable",
            "note": f"No elevation data available: {e}",
        }
        return None, source_info


def _osm_features_to_wgs84(feature_collection: dict[str, Any]) -> dict[str, Any]:
    """Convert OSM features from BNG back to WGS84 for frontend display.

    OSM features store WGS84 coords in _wgs84_coordinates property,
    or we use pyproj to convert BNG coordinates back.
    """
    from app.services.geocoding import bng_to_latlng

    features = feature_collection.get("features", [])
    transformed = []

    for feature in features:
        new_feature = {**feature}
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        geom_type = geom.get("type", "")

        # Use stored WGS84 coords if available
        wgs84_coords = props.get("_wgs84_coordinates")
        if wgs84_coords and geom_type == "LineString":
            new_feature["geometry"] = {
                "type": "LineString",
                "coordinates": wgs84_coords,
            }
        elif geom_type == "LineString":
            coords = geom.get("coordinates", [])
            new_feature["geometry"] = {
                "type": "LineString",
                "coordinates": [
                    [lon, lat]
                    for e, n in coords
                    for lat, lon in [bng_to_latlng(e, n)]
                ],
            }
        elif geom_type == "Polygon":
            coords = geom.get("coordinates", [])
            new_rings = []
            for ring in coords:
                new_rings.append([
                    [lon, lat]
                    for e, n in ring
                    for lat, lon in [bng_to_latlng(e, n)]
                ])
            new_feature["geometry"] = {
                "type": "Polygon",
                "coordinates": new_rings,
            }

        # Remove internal properties
        new_props = {k: v for k, v in props.items() if not k.startswith("_")}
        new_feature["properties"] = new_props
        transformed.append(new_feature)

    return {
        "type": "FeatureCollection",
        "features": transformed,
    }
