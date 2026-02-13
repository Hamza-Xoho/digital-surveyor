"""Vehicle profile endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.vehicles import get_vehicles, load_all_vehicles

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/")
def list_vehicles() -> Any:
    """List all vehicle profiles."""
    return list(load_all_vehicles())


@router.get("/{vehicle_class}")
def get_vehicle(vehicle_class: str) -> Any:
    """Get a single vehicle profile by class name."""
    matches = get_vehicles([vehicle_class])
    if not matches:
        raise HTTPException(
            status_code=404, detail=f"Vehicle class '{vehicle_class}' not found"
        )
    return matches[0]
