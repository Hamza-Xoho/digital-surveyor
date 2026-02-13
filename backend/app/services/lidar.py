"""LiDAR elevation & gradient service — reads Environment Agency DTM GeoTIFFs.

Downloads 1m resolution Digital Terrain Model tiles from the Environment Agency.
Reads elevation at coordinates using rasterio windowed reads.
Computes gradient profiles along approach roads.
"""

import math
import os
import statistics
from typing import Any

import numpy as np

try:
    import rasterio
    from rasterio.windows import Window

    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

from app.core.config import settings


def _bng_to_tile_ref(easting: float, northing: float) -> str:
    """
    Convert BNG coordinates to 5km OS National Grid tile reference.

    E.g. easting=530000, northing=104000 → "TQ30"
    """
    # First-level grid letters (100km squares)
    grid_letters_row = [
        ["SV", "SW", "SX", "SY", "SZ", "TV", "TW"],
        ["SQ", "SR", "SS", "ST", "SU", "TQ", "TR"],
        ["SL", "SM", "SN", "SO", "SP", "TL", "TM"],
        ["SF", "SG", "SH", "SJ", "SK", "TF", "TG"],
        ["SA", "SB", "SC", "SD", "SE", "TA", "TB"],
        ["NV", "NW", "NX", "NY", "NZ", "OV", "OW"],
        ["NQ", "NR", "NS", "NT", "NU", "OQ", "OR"],
        ["NL", "NM", "NN", "NO", "NP", "OL", "OM"],
        ["NF", "NG", "NH", "NJ", "NK", "OF", "OG"],
        ["NA", "NB", "NC", "ND", "NE", "OA", "OB"],
        ["HV", "HW", "HX", "HY", "HZ", "JV", "JW"],
        ["HQ", "HR", "HS", "HT", "HU", "JQ", "JR"],
        ["HL", "HM", "HN", "HO", "HP", "JL", "JM"],
    ]

    e100 = int(easting / 100000)
    n100 = int(northing / 100000)

    if 0 <= e100 < 7 and 0 <= n100 < 13:
        letters = grid_letters_row[n100][e100]
    else:
        return "UNKNOWN"

    # 10km digit within the 100km square
    e_digit = int((easting % 100000) / 10000)
    n_digit = int((northing % 100000) / 10000)

    return f"{letters}{e_digit}{n_digit}"


def find_lidar_tile(easting: float, northing: float, tiles_dir: str | None = None) -> str | None:
    """Find the correct DTM tile file for given BNG coordinates."""
    if tiles_dir is None:
        tiles_dir = settings.LIDAR_TILES_PATH

    if not os.path.isdir(tiles_dir):
        return None

    tile_ref = _bng_to_tile_ref(easting, northing)

    # Try common naming patterns
    patterns = [
        f"{tile_ref}_DTM_1m.tif",
        f"{tile_ref}_DTM_1M.tif",
        f"{tile_ref.lower()}_dtm_1m.tif",
        f"{tile_ref}_DSM_1m.tif",
    ]

    for pattern in patterns:
        path = os.path.join(tiles_dir, pattern)
        if os.path.exists(path):
            return path

    return None


def get_elevation(easting: float, northing: float, tile_path: str) -> float:
    """
    Read single elevation value from GeoTIFF at given BNG coordinates.

    Returns elevation in metres above sea level.
    """
    if not HAS_RASTERIO:
        raise RuntimeError("rasterio not installed — cannot read LiDAR tiles")

    with rasterio.open(tile_path) as src:
        row, col = src.index(easting, northing)
        window = Window(col, row, 1, 1)
        data = src.read(1, window=window)
        value = float(data[0, 0])

        # NoData check
        if src.nodata is not None and value == src.nodata:
            return float("nan")

        return value


def get_gradient_profile(
    path_coords: list[tuple[float, float]],
    tile_path: str,
    sample_interval_m: float = 1.0,
) -> dict[str, Any]:
    """
    Sample elevation at regular intervals along a path.
    Compute gradient between consecutive samples.

    Args:
        path_coords: List of (easting, northing) along the approach road
        tile_path: Path to the LiDAR GeoTIFF tile
        sample_interval_m: Distance between elevation samples

    Returns:
        {
            "samples": [
                {"distance_m": 0, "elevation_m": 45.2, "gradient_pct": 0},
                {"distance_m": 1, "elevation_m": 45.25, "gradient_pct": 5.0},
                ...
            ],
            "max_gradient_pct": 7.2,
            "mean_gradient_pct": 3.1,
            "steep_segments": [
                {"start_m": 45, "end_m": 52, "gradient_pct": 7.2}
            ],
        }
    """
    if not HAS_RASTERIO:
        return _empty_gradient_result("rasterio not installed")

    if len(path_coords) < 2:
        return _empty_gradient_result("Need at least 2 coordinates")

    # Sample elevation at each coordinate
    samples: list[dict[str, Any]] = []
    cumulative_distance = 0.0

    for i, (e, n) in enumerate(path_coords):
        if i > 0:
            prev_e, prev_n = path_coords[i - 1]
            segment_dist = math.sqrt((e - prev_e) ** 2 + (n - prev_n) ** 2)
            cumulative_distance += segment_dist

        try:
            elev = get_elevation(e, n, tile_path)
        except Exception:
            continue

        if math.isnan(elev):
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
            "easting": e,
            "northing": n,
        })

    if not samples:
        return _empty_gradient_result("No valid elevation samples")

    gradients = [s["gradient_pct"] for s in samples if s["gradient_pct"] > 0]

    if not gradients:
        return {
            "samples": samples,
            "max_gradient_pct": 0.0,
            "mean_gradient_pct": 0.0,
            "steep_segments": [],
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
    }


GRADIENT_THRESHOLDS: dict[str, dict[str, float]] = {
    "pantechnicon_18t": {"amber": 5.0, "red": 8.0},
    "truck_7_5t": {"amber": 6.0, "red": 10.0},
    "default": {"amber": 8.0, "red": 12.0},
}


def classify_gradient(gradient_pct: float, vehicle_class: str = "") -> str:
    """
    Classify gradient severity for a vehicle type.

    Uses per-vehicle thresholds — heavier vehicles have stricter limits.
    Returns GREEN, AMBER, or RED.
    """
    thresholds = GRADIENT_THRESHOLDS.get(vehicle_class, GRADIENT_THRESHOLDS["default"])
    if gradient_pct <= thresholds["amber"]:
        return "GREEN"
    elif gradient_pct <= thresholds["red"]:
        return "AMBER"
    else:
        return "RED"


def _empty_gradient_result(reason: str) -> dict[str, Any]:
    """Return empty gradient result with reason."""
    return {
        "samples": [],
        "max_gradient_pct": 0.0,
        "mean_gradient_pct": 0.0,
        "steep_segments": [],
        "error": reason,
    }
