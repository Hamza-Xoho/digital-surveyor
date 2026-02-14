"""Overpass API fallback — free road geometry from OpenStreetMap.

When OS_API_KEY is not configured, this service fetches road geometries
from the Overpass API (free, no key required) and converts them into
a format compatible with the existing width analysis pipeline.

Road widths are estimated from OSM highway classification tags using
UK-standard typical widths (from Manual for Streets / DMRB).
"""

import logging
from typing import Any

import httpx
from pyproj import Transformer

from app.services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_TTL_DAYS = 30

# WGS84 → BNG transformer (for converting OSM coords to match OS pipeline)
_to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

# Typical UK road widths by OSM highway classification (metres)
# Sources: Manual for Streets (MfS), Design Manual for Roads and Bridges (DMRB)
OSM_ROAD_WIDTH_ESTIMATES: dict[str, float] = {
    "motorway": 11.0,
    "motorway_link": 7.3,
    "trunk": 7.3,
    "trunk_link": 6.5,
    "primary": 6.7,
    "primary_link": 6.0,
    "secondary": 6.1,
    "secondary_link": 5.5,
    "tertiary": 5.5,
    "tertiary_link": 5.0,
    "residential": 5.5,
    "living_street": 4.8,
    "unclassified": 5.0,
    "service": 3.7,
    "track": 3.0,
    "path": 1.5,
    "footway": 1.5,
    "cycleway": 2.0,
    "pedestrian": 3.0,
}


def _build_overpass_query(lat: float, lon: float, radius: int = 200) -> str:
    """Build Overpass QL query for highway ways in a bounding box."""
    return f"""
    [out:json][timeout:25];
    (
      way["highway"](around:{radius},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """


def _osm_to_bng_geojson(elements: list[dict], nodes: dict[int, tuple[float, float]]) -> dict[str, Any]:
    """Convert Overpass way elements to BNG-coordinate GeoJSON FeatureCollection.

    Produces output matching the format of OS MasterMap TopographicLine features
    so it can be consumed by the existing width_analysis pipeline.
    """
    features: list[dict[str, Any]] = []

    for element in elements:
        if element.get("type") != "way":
            continue

        tags = element.get("tags", {})
        highway = tags.get("highway", "")
        if not highway:
            continue

        # Build coordinate list from node references
        node_refs = element.get("nodes", [])
        coords_bng: list[list[float]] = []
        coords_wgs84: list[list[float]] = []

        for nid in node_refs:
            if nid in nodes:
                lon, lat = nodes[nid]
                easting, northing = _to_bng.transform(lon, lat)
                coords_bng.append([easting, northing])
                coords_wgs84.append([lon, lat])

        if len(coords_bng) < 2:
            continue

        # Get width from tags or estimate from highway type
        width_str = tags.get("width", "")
        try:
            width = float(width_str.replace("m", "").strip())
        except (ValueError, AttributeError):
            width = OSM_ROAD_WIDTH_ESTIMATES.get(highway, 5.0)

        name = tags.get("name", "")
        surface = tags.get("surface", "")
        oneway = tags.get("oneway", "no")
        lanes_str = tags.get("lanes", "")

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords_bng,
            },
            "properties": {
                "DescriptiveGroup": "Road Or Track",
                "highway": highway,
                "name": name,
                "width_m": width,
                "surface": surface,
                "oneway": oneway,
                "lanes": lanes_str,
                "source": "osm",
                # Store WGS84 coords for frontend display
                "_wgs84_coordinates": coords_wgs84,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "crs": "EPSG:27700",
        "source": "overpass_api",
    }


def _osm_to_area_geojson(elements: list[dict], nodes: dict[int, tuple[float, float]]) -> dict[str, Any]:
    """Convert closed ways (buildings, areas) to polygon GeoJSON features."""
    features: list[dict[str, Any]] = []

    for element in elements:
        if element.get("type") != "way":
            continue

        tags = element.get("tags", {})
        node_refs = element.get("nodes", [])

        # Check if it's a closed way (polygon)
        if len(node_refs) < 4 or node_refs[0] != node_refs[-1]:
            continue

        building = tags.get("building")
        if not building:
            continue

        coords_bng: list[list[float]] = []
        for nid in node_refs:
            if nid in nodes:
                lon, lat = nodes[nid]
                easting, northing = _to_bng.transform(lon, lat)
                coords_bng.append([easting, northing])

        if len(coords_bng) < 4:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords_bng],
            },
            "properties": {
                "DescriptiveGroup": "Building",
                "building": building,
                "name": tags.get("name", ""),
                "source": "osm",
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "crs": "EPSG:27700",
        "source": "overpass_api",
    }


async def fetch_osm_road_features(
    lat: float,
    lon: float,
    radius: int = 200,
) -> dict[str, Any]:
    """Fetch road geometries from Overpass API (free, no key needed).

    Returns GeoJSON FeatureCollection in BNG coordinates matching
    the format expected by compute_road_widths().
    """
    cache_key = f"overpass_roads:{round(lat, 5)}:{round(lon, 5)}:{radius}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    query = _build_overpass_query(lat, lon, radius)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("Overpass API unavailable: %s", e)
        return {"type": "FeatureCollection", "features": [], "error": str(e)}
    except httpx.HTTPStatusError as e:
        logger.warning("Overpass API returned %s: %s", e.response.status_code, e)
        return {"type": "FeatureCollection", "features": [], "error": str(e)}

    elements = data.get("elements", [])

    # Build node lookup (id → (lon, lat))
    nodes: dict[int, tuple[float, float]] = {}
    for el in elements:
        if el.get("type") == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])

    result = _osm_to_bng_geojson(elements, nodes)
    result["feature_count"] = len(result["features"])

    set_cached(cache_key, result, ttl_days=CACHE_TTL_DAYS)
    return result


async def fetch_osm_building_features(
    lat: float,
    lon: float,
    radius: int = 200,
) -> dict[str, Any]:
    """Fetch building footprints from Overpass API.

    Returns GeoJSON FeatureCollection of building polygons in BNG coordinates.
    """
    cache_key = f"overpass_buildings:{round(lat, 5)}:{round(lon, 5)}:{radius}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    query = f"""
    [out:json][timeout:25];
    (
      way["building"](around:{radius},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("Overpass API unavailable for buildings: %s", e)
        return {"type": "FeatureCollection", "features": [], "error": str(e)}
    except httpx.HTTPStatusError as e:
        logger.warning("Overpass API returned %s for buildings", e.response.status_code)
        return {"type": "FeatureCollection", "features": [], "error": str(e)}

    elements = data.get("elements", [])
    nodes: dict[int, tuple[float, float]] = {}
    for el in elements:
        if el.get("type") == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])

    result = _osm_to_area_geojson(elements, nodes)
    result["feature_count"] = len(result["features"])

    set_cached(cache_key, result, ttl_days=CACHE_TTL_DAYS)
    return result


def compute_road_widths_from_osm(line_features: dict[str, Any]) -> dict[str, Any]:
    """Compute road widths from OSM tagged width values or highway-type estimates.

    Unlike the OS MasterMap approach (which measures perpendicular distances
    between opposing kerb-edge lines), OSM roads are centrelines with width
    as a tag or estimated from highway classification.

    Returns dict matching compute_road_widths() output format.
    """
    features = line_features.get("features", [])

    if not features:
        return {
            "min_width_m": 0.0,
            "max_width_m": 0.0,
            "mean_width_m": 0.0,
            "sample_count": 0,
            "pinch_points": [],
            "measurements": [],
            "measurement_lines_geojson": {"type": "FeatureCollection", "features": []},
            "source": "osm",
            "error": "No OSM road features available",
        }

    # Filter to actual roads (not footways/cycleways for vehicle access)
    vehicle_roads = [
        f for f in features
        if f.get("properties", {}).get("highway", "") in {
            "motorway", "motorway_link", "trunk", "trunk_link",
            "primary", "primary_link", "secondary", "secondary_link",
            "tertiary", "tertiary_link", "residential", "living_street",
            "unclassified", "service",
        }
    ]

    if not vehicle_roads:
        vehicle_roads = features  # Fall back to all features

    widths: list[float] = []
    measurements: list[dict[str, Any]] = []

    for feature in vehicle_roads:
        props = feature.get("properties", {})
        width = props.get("width_m", 5.0)
        widths.append(width)

        # Create a pseudo-measurement at the midpoint of each road segment
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2:
            mid_idx = len(coords) // 2
            mid_point = coords[mid_idx]
            measurements.append({
                "fraction": 0.5,
                "width_m": round(width, 2),
                "left_point": mid_point,
                "right_point": mid_point,
                "highway": props.get("highway", ""),
                "name": props.get("name", ""),
            })

    if not widths:
        return {
            "min_width_m": 0.0,
            "max_width_m": 0.0,
            "mean_width_m": 0.0,
            "sample_count": 0,
            "pinch_points": [],
            "measurements": [],
            "measurement_lines_geojson": {"type": "FeatureCollection", "features": []},
            "source": "osm",
            "error": "No width data from OSM features",
        }

    min_w = min(widths)
    max_w = max(widths)
    mean_w = sum(widths) / len(widths)

    # Pinch points are the narrowest roads
    threshold = sorted(widths)[max(1, len(widths) // 10) - 1]
    pinch_points = [
        {"location": m["left_point"], "width_m": m["width_m"]}
        for m in measurements
        if m["width_m"] <= threshold
    ]

    return {
        "min_width_m": round(min_w, 2),
        "max_width_m": round(max_w, 2),
        "mean_width_m": round(mean_w, 2),
        "sample_count": len(measurements),
        "pinch_points": pinch_points,
        "measurements": measurements,
        "measurement_lines_geojson": {"type": "FeatureCollection", "features": []},
        "source": "osm",
        "note": "Widths estimated from OSM highway classification tags",
    }
