"""Open Elevation API fallback — free elevation data when LiDAR tiles unavailable.

Uses the Open-Meteo Elevation API (free, no key required) to get elevation
at coordinates. Falls back to Open Elevation API if Open-Meteo is unavailable.

Both services return SRTM-derived elevation data at ~30m resolution,
which is coarser than Environment Agency 1m LiDAR but sufficient for
gradient classification (steep vs. flat approach roads).
"""

import logging
import math
import statistics
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Open-Meteo: free, fast, no key, 10000 req/day
OPEN_METEO_URL = "https://api.open-meteo.com/v1/elevation"

# Open Elevation: free, no key, community-hosted
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"


async def _get_elevation_open_meteo(
    points: list[tuple[float, float]],
) -> list[float | None]:
    """Fetch elevations from Open-Meteo API.

    Args:
        points: List of (latitude, longitude) tuples

    Returns:
        List of elevation values (metres) or None for failures
    """
    if not points:
        return []

    lats = ",".join(str(round(p[0], 6)) for p in points)
    lons = ",".join(str(round(p[1], 6)) for p in points)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                OPEN_METEO_URL,
                params={"latitude": lats, "longitude": lons},
            )
            resp.raise_for_status()
            data = resp.json()

        elevations = data.get("elevation", [])
        return [float(e) if e is not None else None for e in elevations]

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("Open-Meteo elevation API unavailable: %s", e)
        return [None] * len(points)
    except (httpx.HTTPStatusError, KeyError, ValueError) as e:
        logger.warning("Open-Meteo elevation API error: %s", e)
        return [None] * len(points)


async def _get_elevation_open_elevation(
    points: list[tuple[float, float]],
) -> list[float | None]:
    """Fetch elevations from Open Elevation API (backup).

    Args:
        points: List of (latitude, longitude) tuples

    Returns:
        List of elevation values (metres) or None for failures
    """
    if not points:
        return []

    locations = [{"latitude": p[0], "longitude": p[1]} for p in points]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                OPEN_ELEVATION_URL,
                json={"locations": locations},
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        return [float(r.get("elevation", 0)) for r in results]

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("Open Elevation API unavailable: %s", e)
        return [None] * len(points)
    except (httpx.HTTPStatusError, KeyError, ValueError) as e:
        logger.warning("Open Elevation API error: %s", e)
        return [None] * len(points)


async def get_elevations(
    points: list[tuple[float, float]],
) -> list[float | None]:
    """Get elevations for a list of (lat, lon) points.

    Tries Open-Meteo first, falls back to Open Elevation API.
    """
    elevations = await _get_elevation_open_meteo(points)

    # Check if we got valid results
    valid_count = sum(1 for e in elevations if e is not None)
    if valid_count < len(points) // 2:
        logger.info("Open-Meteo returned too few results, trying Open Elevation API")
        backup = await _get_elevation_open_elevation(points)
        # Merge: prefer Open-Meteo values, fill gaps from backup
        for i in range(len(elevations)):
            if elevations[i] is None and i < len(backup):
                elevations[i] = backup[i]

    return elevations


async def get_gradient_profile_from_api(
    path_coords_wgs84: list[tuple[float, float]],
    sample_interval_m: float = 10.0,
) -> dict[str, Any]:
    """Compute gradient profile using free elevation APIs.

    Similar to lidar.get_gradient_profile() but uses API-sourced elevation
    at coarser resolution (~30m SRTM vs 1m LiDAR).

    Args:
        path_coords_wgs84: List of (latitude, longitude) along approach road
        sample_interval_m: Desired distance between samples (minimum ~30m due to SRTM)

    Returns:
        Dict matching the lidar gradient result format.
    """
    if len(path_coords_wgs84) < 2:
        return _empty_result("Need at least 2 coordinates")

    # Get elevations for all path points
    elevations = await get_elevations(path_coords_wgs84)

    # Build samples with distance calculation
    samples: list[dict[str, Any]] = []
    cumulative_distance = 0.0

    for i, (lat, lon) in enumerate(path_coords_wgs84):
        if i > 0:
            prev_lat, prev_lon = path_coords_wgs84[i - 1]
            segment_dist = _haversine_m(prev_lat, prev_lon, lat, lon)
            cumulative_distance += segment_dist

        elev = elevations[i] if i < len(elevations) else None
        if elev is None:
            continue

        gradient_pct = 0.0
        if samples:
            prev = samples[-1]
            dist_diff = cumulative_distance - prev["distance_m"]
            if dist_diff > 0:
                elev_diff = elev - prev["elevation_m"]
                gradient_pct = abs(elev_diff / dist_diff) * 100

        samples.append({
            "distance_m": round(cumulative_distance, 1),
            "elevation_m": round(elev, 2),
            "gradient_pct": round(gradient_pct, 1),
            "latitude": lat,
            "longitude": lon,
        })

    if not samples:
        return _empty_result("No valid elevation samples from API")

    gradients = [s["gradient_pct"] for s in samples if s["gradient_pct"] > 0]

    if not gradients:
        return {
            "samples": samples,
            "max_gradient_pct": 0.0,
            "mean_gradient_pct": 0.0,
            "steep_segments": [],
            "source": "elevation_api",
        }

    # Find steep segments (gradient > 5%)
    steep_segments: list[dict[str, Any]] = []
    in_steep = False
    steep_start = 0.0

    for s in samples:
        if s["gradient_pct"] > 5.0:
            if not in_steep:
                steep_start = s["distance_m"]
                in_steep = True
        elif in_steep:
            steep_segments.append({
                "start_m": steep_start,
                "end_m": s["distance_m"],
                "gradient_pct": round(max(
                    ss["gradient_pct"]
                    for ss in samples
                    if steep_start <= ss["distance_m"] <= s["distance_m"]
                ), 1),
            })
            in_steep = False

    return {
        "samples": samples,
        "max_gradient_pct": round(max(gradients), 1),
        "mean_gradient_pct": round(statistics.mean(gradients), 1),
        "steep_segments": steep_segments,
        "source": "elevation_api",
        "note": "Elevation from SRTM (~30m resolution)",
    }


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two WGS84 points in metres."""
    R = 6_371_000  # Earth radius in metres
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _empty_result(reason: str) -> dict[str, Any]:
    """Return empty gradient result with reason."""
    return {
        "samples": [],
        "max_gradient_pct": 0.0,
        "mean_gradient_pct": 0.0,
        "steep_segments": [],
        "source": "elevation_api",
        "error": reason,
    }
