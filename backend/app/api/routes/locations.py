"""Saved location endpoints — save and manage frequently assessed locations."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.crud import (
    create_saved_location,
    delete_saved_location,
    list_saved_locations,
    update_saved_location,
)
from app.services.geocoding import geocode_postcode

router = APIRouter(prefix="/locations", tags=["locations"])


class LocationCreate(BaseModel):
    label: str
    postcode: str
    notes: str | None = None


class LocationUpdate(BaseModel):
    label: str | None = None
    notes: str | None = None


@router.get("/")
def list_locations(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """List saved locations for the current user."""
    locations = list_saved_locations(session=session, owner_id=current_user.id)
    return [
        {
            "id": str(loc.id),
            "label": loc.label,
            "postcode": loc.postcode,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "notes": loc.notes,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


@router.post("/")
async def create_location(
    body: LocationCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Save a new location by postcode. Geocodes automatically."""
    coords = await geocode_postcode(body.postcode)

    location = create_saved_location(
        session=session,
        owner_id=current_user.id,
        label=body.label,
        postcode=coords["postcode"],
        latitude=coords["latitude"],
        longitude=coords["longitude"],
        notes=body.notes,
    )

    return {
        "id": str(location.id),
        "label": location.label,
        "postcode": location.postcode,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "notes": location.notes,
        "created_at": location.created_at,
    }


@router.patch("/{location_id}")
def update_location(
    location_id: uuid.UUID,
    body: LocationUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Update a saved location's label or notes."""
    location = update_saved_location(
        session=session,
        location_id=location_id,
        owner_id=current_user.id,
        label=body.label,
        notes=body.notes,
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return {
        "id": str(location.id),
        "label": location.label,
        "postcode": location.postcode,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "notes": location.notes,
        "created_at": location.created_at,
    }


@router.delete("/{location_id}")
def delete_location(
    location_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Delete a saved location."""
    deleted = delete_saved_location(
        session=session,
        location_id=location_id,
        owner_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted"}
