"""Vehicle profile endpoints — static defaults + custom profiles."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, SessionDep
from app.crud import (
    create_vehicle_profile,
    delete_vehicle_profile,
    list_vehicle_profiles,
)
from app.services.vehicles import get_vehicles, load_all_vehicles

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/")
def list_vehicles() -> Any:
    """List all default vehicle profiles."""
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


# --- Custom vehicle profiles ---


class VehicleCreate(BaseModel):
    name: str = Field(max_length=100)
    vehicle_class: str = Field(max_length=50)
    width_m: float = Field(gt=0, le=10)
    length_m: float = Field(gt=0, le=30)
    height_m: float = Field(gt=0, le=10)
    weight_kg: int = Field(gt=0, le=100000)
    turning_radius_m: float = Field(gt=0, le=30)
    mirror_width_m: float = Field(default=0.25, ge=0, le=1)


@router.get("/custom/list")
def list_custom_vehicles(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """List all custom vehicle profiles."""
    return [
        {
            "id": str(v.id),
            "name": v.name,
            "vehicle_class": v.vehicle_class,
            "width_m": v.width_m,
            "length_m": v.length_m,
            "height_m": v.height_m,
            "weight_kg": v.weight_kg,
            "turning_radius_m": v.turning_radius_m,
            "mirror_width_m": v.mirror_width_m,
            "created_at": v.created_at,
        }
        for v in list_vehicle_profiles(session=session)
    ]


@router.post("/custom")
def create_custom_vehicle(
    body: VehicleCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Create a custom vehicle profile."""
    vehicle = create_vehicle_profile(
        session=session,
        name=body.name,
        vehicle_class=body.vehicle_class,
        width_m=body.width_m,
        length_m=body.length_m,
        height_m=body.height_m,
        weight_kg=body.weight_kg,
        turning_radius_m=body.turning_radius_m,
        mirror_width_m=body.mirror_width_m,
    )
    return {
        "id": str(vehicle.id),
        "name": vehicle.name,
        "vehicle_class": vehicle.vehicle_class,
        "width_m": vehicle.width_m,
        "length_m": vehicle.length_m,
        "height_m": vehicle.height_m,
        "weight_kg": vehicle.weight_kg,
        "turning_radius_m": vehicle.turning_radius_m,
        "mirror_width_m": vehicle.mirror_width_m,
    }


@router.delete("/custom/{vehicle_id}")
def delete_custom_vehicle(
    vehicle_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Delete a custom vehicle profile."""
    deleted = delete_vehicle_profile(session=session, vehicle_id=vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    return {"message": "Deleted"}
