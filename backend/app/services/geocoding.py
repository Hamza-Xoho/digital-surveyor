"""Geocoding service — converts UK postcodes to coordinates.

Uses postcodes.io (free, no API key) as primary source.
Caches results in GeoCache table with 30-day TTL.
Includes BNG <-> WGS84 coordinate transforms via pyproj.
"""

import re

import httpx
from pyproj import Transformer

from app.errors import InvalidPostcodeError, PostcodeNotFoundError
from app.services.cache import get_cached, set_cached

# UK postcode regex
UK_POSTCODE_RE = re.compile(
    r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", re.IGNORECASE
)

# Coordinate transformers (thread-safe, reusable)
_to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
_to_wgs = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

POSTCODES_IO_URL = "https://api.postcodes.io/postcodes"
CACHE_TTL_DAYS = 30


def latlng_to_bng(lat: float, lon: float) -> tuple[float, float]:
    """Convert WGS84 lat/lon to British National Grid easting/northing."""
    easting, northing = _to_bng.transform(lon, lat)
    return easting, northing


def bng_to_latlng(easting: float, northing: float) -> tuple[float, float]:
    """Convert British National Grid to WGS84 lat/lon."""
    lon, lat = _to_wgs.transform(easting, northing)
    return lat, lon


def normalise_postcode(postcode: str) -> str:
    """Normalise UK postcode to uppercase with single space."""
    clean = postcode.upper().strip().replace(" ", "")
    if len(clean) < 5:
        return clean
    return clean[:-3] + " " + clean[-3:]


def validate_postcode(postcode: str) -> bool:
    """Check if string looks like a valid UK postcode."""
    return bool(UK_POSTCODE_RE.match(postcode.strip()))


async def geocode_postcode(postcode: str) -> dict:
    """
    Geocode a UK postcode using postcodes.io (free, no API key).

    Returns dict with postcode, latitude, longitude, easting, northing.

    Raises:
        InvalidPostcodeError: If postcode fails format validation.
        PostcodeNotFoundError: If postcode not found by postcodes.io.
    """
    normalised = normalise_postcode(postcode)

    if not validate_postcode(normalised):
        raise InvalidPostcodeError(f"Invalid UK postcode: {postcode}")

    cache_key = f"geocode:{normalised}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"{POSTCODES_IO_URL}/{normalised.replace(' ', '%20')}"
        resp = await client.get(url)

    if resp.status_code == 404:
        raise PostcodeNotFoundError(f"Postcode not found: {normalised}")
    resp.raise_for_status()

    data = resp.json()
    result_data = data["result"]

    result = {
        "postcode": result_data["postcode"],
        "latitude": result_data["latitude"],
        "longitude": result_data["longitude"],
        "easting": result_data["eastings"],
        "northing": result_data["northings"],
    }

    set_cached(cache_key, result, ttl_days=CACHE_TTL_DAYS)
    return result
