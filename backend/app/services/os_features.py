"""OS Features API service — fetches MasterMap road edges and building footprints.

Queries the Ordnance Survey Features API (WFS) for TopographicArea and
TopographicLine features within a bounding box around given BNG coordinates.
Handles pagination (100 features/page max), caching (90-day TTL), and
coordinate transforms for frontend display.
"""

from typing import Any

import httpx

from app.core.config import settings
from app.schemas.geodata import BoundingBox
from app.services.cache import get_cached, set_cached
from app.services.geocoding import bng_to_latlng

OS_FEATURES_URL = "https://api.os.uk/features/v1/wfs"
CACHE_TTL_DAYS = 90
MAX_FEATURES_PER_PAGE = 100
MAX_PAGES = 10  # Safety limit

# Feature types we care about
KEEP_DESCRIPTIVE_GROUPS = {
    "Road Or Track",
    "Building",
    "Path",
    "General Surface",
}


async def _fetch_wfs_features(
    type_names: str,
    bbox: BoundingBox,
    api_key: str,
) -> list[dict[str, Any]]:
    """
    Fetch features from OS Features API with pagination.

    Args:
        type_names: WFS typeName (e.g. "Topography_TopographicArea")
        bbox: Bounding box in BNG coordinates
        api_key: OS Data Hub API key

    Returns:
        List of GeoJSON features
    """
    all_features: list[dict] = []
    start_index = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _page in range(MAX_PAGES):
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": type_names,
                "outputFormat": "GEOJSON",
                "srsName": "EPSG:27700",
                "bbox": bbox.to_wfs_bbox(),
                "count": MAX_FEATURES_PER_PAGE,
                "startIndex": start_index,
                "key": api_key,
            }

            resp = await client.get(OS_FEATURES_URL, params=params)
            resp.raise_for_status()

            data = resp.json()
            features = data.get("features", [])

            if not features:
                break

            all_features.extend(features)
            start_index += len(features)

            # If we got fewer than max, we've reached the end
            if len(features) < MAX_FEATURES_PER_PAGE:
                break

    return all_features


def _filter_features(
    features: list[dict[str, Any]],
    keep_groups: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Filter features by DescriptiveGroup property."""
    if keep_groups is None:
        keep_groups = KEEP_DESCRIPTIVE_GROUPS
    return [
        f
        for f in features
        if f.get("properties", {}).get("DescriptiveGroup", "") in keep_groups
    ]


def _transform_coord_pair(pair: list[float]) -> list[float]:
    """Transform a single [easting, northing] pair to [longitude, latitude]."""
    lat, lon = bng_to_latlng(pair[0], pair[1])
    return [lon, lat]


def _transform_ring(ring: list[list[float]]) -> list[list[float]]:
    """Transform a polygon ring (list of coordinate pairs) from BNG to WGS84."""
    return [_transform_coord_pair(c) for c in ring if len(c) >= 2]


def _transform_features_to_wgs84(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform feature coordinates from BNG (EPSG:27700) to WGS84 (EPSG:4326).

    Handles Point, LineString, MultiLineString, Polygon, and MultiPolygon geometries.
    """
    transformed = []
    for feature in features:
        geom = feature.get("geometry", {})
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates", [])

        new_feature = {**feature}
        new_geom = {**geom}

        if geom_type == "Point" and len(coords) >= 2:
            new_geom["coordinates"] = _transform_coord_pair(coords)
        elif geom_type == "LineString":
            new_geom["coordinates"] = [
                _transform_coord_pair(c) for c in coords if len(c) >= 2
            ]
        elif geom_type == "MultiLineString":
            new_geom["coordinates"] = [
                [_transform_coord_pair(c) for c in line if len(c) >= 2]
                for line in coords
            ]
        elif geom_type == "Polygon":
            new_geom["coordinates"] = [_transform_ring(ring) for ring in coords]
        elif geom_type == "MultiPolygon":
            new_geom["coordinates"] = [
                [_transform_ring(ring) for ring in polygon]
                for polygon in coords
            ]

        new_feature["geometry"] = new_geom
        transformed.append(new_feature)

    return transformed


def get_features_wgs84(feature_collection: dict[str, Any]) -> dict[str, Any]:
    """Transform all features in a FeatureCollection from BNG to WGS84."""
    features = feature_collection.get("features", [])
    transformed = _transform_features_to_wgs84(features)
    return {
        "type": "FeatureCollection",
        "features": transformed,
    }


async def fetch_area_features(
    easting: float,
    northing: float,
    radius: int = 200,
) -> dict[str, Any]:
    """
    Fetch OS MasterMap TopographicArea features (polygons) around coordinates.

    Returns GeoJSON FeatureCollection with roads, buildings, paths, surfaces.
    """
    api_key = settings.OS_API_KEY
    if not api_key:
        return {"type": "FeatureCollection", "features": [], "note": "OS_API_KEY not configured"}

    bbox = BoundingBox.from_centre(easting, northing, radius)
    cache_key = f"os_area:{int(easting)}:{int(northing)}:{radius}"

    cached = get_cached(cache_key)
    if cached:
        return cached

    raw_features = await _fetch_wfs_features(
        "Topography_TopographicArea", bbox, api_key
    )
    filtered = _filter_features(raw_features)

    result = {
        "type": "FeatureCollection",
        "features": filtered,
        "feature_count": len(filtered),
        "crs": "EPSG:27700",
    }

    set_cached(cache_key, result, ttl_days=CACHE_TTL_DAYS)
    return result


async def fetch_line_features(
    easting: float,
    northing: float,
    radius: int = 200,
) -> dict[str, Any]:
    """
    Fetch OS MasterMap TopographicLine features (road edges, kerb lines).

    Returns GeoJSON FeatureCollection.
    """
    api_key = settings.OS_API_KEY
    if not api_key:
        return {"type": "FeatureCollection", "features": [], "note": "OS_API_KEY not configured"}

    bbox = BoundingBox.from_centre(easting, northing, radius)
    cache_key = f"os_line:{int(easting)}:{int(northing)}:{radius}"

    cached = get_cached(cache_key)
    if cached:
        return cached

    raw_features = await _fetch_wfs_features(
        "Topography_TopographicLine", bbox, api_key
    )

    # For lines, keep road-related features
    road_lines = [
        f
        for f in raw_features
        if f.get("properties", {}).get("DescriptiveGroup", "") in {"Road Or Track", "Path"}
    ]

    result = {
        "type": "FeatureCollection",
        "features": road_lines,
        "feature_count": len(road_lines),
        "crs": "EPSG:27700",
    }

    set_cached(cache_key, result, ttl_days=CACHE_TTL_DAYS)
    return result
