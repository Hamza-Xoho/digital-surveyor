import logging
from typing import Any

from app.services.lidar import classify_gradient
from app.services.width_analysis import check_vehicle_width_fit

logger = logging.getLogger(__name__)


def score_vehicle_access(
    vehicle: dict,
    width_result: dict | None,
    gradient_result: dict | None,
    turning_result: dict | None,
    route_restrictions: dict | None,
) -> dict[str, Any]:
    """
    Aggregate all checks into a final Green/Amber/Red rating.

    Logic:
    - Collect individual check ratings
    - Overall = worst individual rating
    - Confidence = fraction of checks that had data available
    """
    checks = []
    data_available = 0
    total_checks = 4

    # 1. Road Width Check
    if width_result and width_result.get("min_width_m", 0) > 0:
        fit = check_vehicle_width_fit(
            width_result["min_width_m"],
            vehicle["width_m"],
            vehicle.get("mirror_width_m", 0.25),
        )
        checks.append({
            "name": "Road Width",
            "rating": fit["rating"],
            "detail": (
                f"{fit['available_width_m']}m available, "
                f"{fit['total_vehicle_width_m']}m vehicle width, "
                f"{fit['clearance_m']}m clearance"
            ),
            "value": fit["available_width_m"],
            "threshold": fit["total_vehicle_width_m"],
        })
        data_available += 1
    else:
        checks.append({
            "name": "Road Width",
            "rating": "AMBER",
            "detail": "Width data unavailable — manual check recommended",
            "value": None,
            "threshold": None,
        })

    # 2. Gradient Check
    if gradient_result and gradient_result.get("max_gradient_pct", 0) > 0:
        grad_rating = classify_gradient(
            gradient_result["max_gradient_pct"],
            vehicle.get("vehicle_class", ""),
        )
        checks.append({
            "name": "Gradient",
            "rating": grad_rating,
            "detail": (
                f"Max {gradient_result['max_gradient_pct']}% gradient, "
                f"mean {gradient_result['mean_gradient_pct']}%"
            ),
            "value": gradient_result["max_gradient_pct"],
            "threshold": 5.0,
        })
        data_available += 1
    else:
        checks.append({
            "name": "Gradient",
            "rating": "AMBER",
            "detail": "LiDAR data unavailable — gradient not assessed",
            "value": None,
            "threshold": None,
        })

    # 3. Turning Space Check
    if turning_result and turning_result.get("assessed"):
        checks.append({
            "name": "Turning Space",
            "rating": turning_result["rating"],
            "detail": turning_result["detail"],
            "value": turning_result.get("available_radius_m"),
            "threshold": turning_result.get("required_radius_m"),
        })
        data_available += 1
    else:
        checks.append({
            "name": "Turning Space",
            "rating": "GREEN",
            "detail": "Not a dead-end — turning space not required",
            "value": None,
            "threshold": None,
        })
        data_available += 1  # Not needed = counts as available

    # 4. Height / Weight Restrictions Check
    if route_restrictions:
        checks.append({
            "name": "Route Restrictions",
            "rating": route_restrictions["rating"],
            "detail": (
                "; ".join(route_restrictions.get("warnings", []))
                if route_restrictions.get("warnings")
                else "No restrictions found on route"
            ),
            "value": None,
            "threshold": None,
        })
        data_available += 1
    else:
        checks.append({
            "name": "Route Restrictions",
            "rating": "AMBER",
            "detail": "Routing check unavailable — check for low bridges manually",
            "value": None,
            "threshold": None,
        })

    # Compute overall rating (worst of all checks)
    ratings = [c["rating"] for c in checks]
    if "RED" in ratings:
        overall = "RED"
    elif "AMBER" in ratings:
        overall = "AMBER"
    else:
        overall = "GREEN"

    # Confidence score
    confidence = round(data_available / total_checks, 2)

    # Recommendation text
    if overall == "GREEN":
        recommendation = f"Access clear for {vehicle['name']} — all checks passed"
    elif overall == "RED":
        red_checks = [c["name"] for c in checks if c["rating"] == "RED"]
        recommendation = (
            f"{vehicle['name']} CANNOT access this property — "
            f"failed: {', '.join(red_checks)}"
        )
    else:
        amber_checks = [c["name"] for c in checks if c["rating"] == "AMBER"]
        recommendation = (
            f"{vehicle['name']} access possible with caution — "
            f"concerns: {', '.join(amber_checks)}"
        )

    return {
        "vehicle_name": vehicle["name"],
        "vehicle_class": vehicle.get("vehicle_class", ""),
        "overall_rating": overall,
        "confidence": confidence,
        "checks": checks,
        "recommendation": recommendation,
    }
