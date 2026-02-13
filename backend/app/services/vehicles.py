"""Vehicle profile loader — single source of truth."""

import json
from functools import lru_cache
from pathlib import Path

VEHICLES_PATH = Path(__file__).resolve().parent.parent / "data" / "vehicles.json"


@lru_cache(maxsize=1)
def load_all_vehicles() -> tuple[dict, ...]:
    """Load vehicle profiles from JSON. Cached after first call."""
    with open(VEHICLES_PATH) as f:
        return tuple(json.load(f))


def get_vehicles(vehicle_classes: list[str] | None = None) -> list[dict]:
    """Get vehicles, optionally filtered by class name."""
    all_vehicles = list(load_all_vehicles())
    if vehicle_classes:
        return [v for v in all_vehicles if v["vehicle_class"] in vehicle_classes]
    return all_vehicles
