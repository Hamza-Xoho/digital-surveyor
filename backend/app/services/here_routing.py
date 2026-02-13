import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)

HERE_ROUTER_URL = "https://router.hereapi.com/v8/routes"
CACHE_TTL_DAYS = 7


async def check_truck_restrictions(
    origin: tuple[float, float],
    destination: tuple[float, float],
    vehicle_height_m: float = 4.0,
    vehicle_width_m: float = 2.55,
    vehicle_weight_kg: int = 18000,
    api_key: str = "",
) -> dict[str, Any]:
    """
    Check truck routing restrictions using HERE API v8.

    Returns restrictions (low bridges, weight limits, width limits)
    along the route from origin to destination.
    """
    if not api_key:
        api_key = settings.HERE_API_KEY
    if not api_key:
        return {
            "route_found": False,
            "restrictions": [],
            "warnings": ["HERE API key not configured — restriction check skipped"],
            "rating": "AMBER",
        }

    cache_key = (
        f"here:{origin[0]:.4f},{origin[1]:.4f}:"
        f"{destination[0]:.4f},{destination[1]:.4f}:"
        f"h{vehicle_height_m}:w{vehicle_width_m}:wt{vehicle_weight_kg}"
    )
    cached = get_cached(cache_key)
    if cached:
        return cached

    params = {
        "transportMode": "truck",
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        "truck[height]": int(vehicle_height_m * 100),
        "truck[width]": int(vehicle_width_m * 100),
        "truck[grossWeight]": vehicle_weight_kg,
        "return": "summary,notices",
        "apiKey": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(HERE_ROUTER_URL, params=params)

        if response.status_code == 400:
            return {
                "route_found": False,
                "restrictions": [],
                "warnings": ["No viable truck route found by HERE API"],
                "rating": "RED",
            }

        response.raise_for_status()
        data = response.json()

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("HERE API unavailable: %s", e)
        return {
            "route_found": False,
            "restrictions": [],
            "warnings": [f"HERE routing service unavailable: {e}"],
            "rating": "AMBER",
        }

    routes = data.get("routes", [])
    if not routes:
        return {
            "route_found": False,
            "restrictions": [],
            "warnings": ["No route found"],
            "rating": "RED",
        }

    route = routes[0]
    notices = []
    restrictions = []

    for section in route.get("sections", []):
        for notice in section.get("notices", []):
            notice_text = notice.get("title", notice.get("code", "Unknown restriction"))
            notices.append(notice_text)

            if "height" in notice_text.lower() or "bridge" in notice_text.lower():
                restrictions.append({"type": "height", "detail": notice_text})
            elif "weight" in notice_text.lower():
                restrictions.append({"type": "weight", "detail": notice_text})
            elif "width" in notice_text.lower():
                restrictions.append({"type": "width", "detail": notice_text})

    rating = "RED" if restrictions else "GREEN"

    result = {
        "route_found": True,
        "restrictions": restrictions,
        "warnings": notices if notices else [],
        "rating": rating,
    }

    set_cached(cache_key, result, ttl_days=CACHE_TTL_DAYS)
    return result
