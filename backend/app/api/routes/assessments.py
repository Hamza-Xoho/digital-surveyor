"""Assessment endpoints — run new assessments and retrieve history."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep
from app.crud import create_assessment, get_assessment, list_assessments
from app.errors import ExternalAPIError, InvalidPostcodeError, PostcodeNotFoundError
from app.services.geocoding import geocode_postcode
from app.services.os_features import fetch_area_features, fetch_line_features, get_features_wgs84
from app.services.pipeline import run_full_assessment

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/quick")
async def quick_assessment(
    postcode: str = Query(..., description="UK postcode e.g. BN1 1AB"),
    vehicle_classes: list[str] | None = Query(None, description="Filter by vehicle class names"),
) -> Any:
    """
    Full access assessment for a UK postcode.
    Returns Green/Amber/Red rating per vehicle class with GeoJSON overlays.
    """
    try:
        result = await run_full_assessment(postcode, vehicle_classes=vehicle_classes)
    except (InvalidPostcodeError, PostcodeNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment pipeline error: {e}")

    return result


@router.post("/")
async def create_and_persist_assessment(
    session: SessionDep,
    current_user: CurrentUser,
    postcode: str = Query(..., description="UK postcode e.g. BN1 1AB"),
    vehicle_classes: list[str] | None = Query(None, description="Filter by vehicle class names"),
) -> Any:
    """
    Run a full assessment and persist the results for the authenticated user.
    """
    try:
        result = await run_full_assessment(postcode, vehicle_classes=vehicle_classes)
    except (InvalidPostcodeError, PostcodeNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment pipeline error: {e}")

    assessment = create_assessment(
        session=session,
        owner_id=current_user.id,
        postcode=result["postcode"],
        latitude=result["latitude"],
        longitude=result["longitude"],
        easting=result["easting"],
        northing=result["northing"],
        overall_rating=result["overall_rating"],
        results=result,
    )

    return {
        "id": str(assessment.id),
        "created_at": assessment.created_at,
        **result,
    }


@router.get("/geodata/{postcode}")
async def get_geodata(postcode: str) -> Any:
    """
    Returns raw OS MasterMap GeoJSON around a postcode.
    For debugging and verifying the OS API integration.
    """
    try:
        coords = await geocode_postcode(postcode)
    except (InvalidPostcodeError, PostcodeNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    area_features = await fetch_area_features(coords["easting"], coords["northing"])
    line_features = await fetch_line_features(coords["easting"], coords["northing"])

    all_features = area_features.get("features", []) + line_features.get("features", [])

    return {
        "postcode": coords["postcode"],
        "centre": {"lat": coords["latitude"], "lon": coords["longitude"]},
        "feature_count": len(all_features),
        "area_feature_count": len(area_features.get("features", [])),
        "line_feature_count": len(line_features.get("features", [])),
        "features_geojson": {
            "type": "FeatureCollection",
            "features": all_features,
        },
        "features_geojson_wgs84": get_features_wgs84({
            "type": "FeatureCollection",
            "features": all_features,
        }),
    }


@router.get("/")
def list_user_assessments(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List past assessments for the current user."""
    items, total = list_assessments(
        session=session,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return {
        "data": [
            {
                "id": str(a.id),
                "postcode": a.postcode,
                "overall_rating": a.overall_rating,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "created_at": a.created_at,
            }
            for a in items
        ],
        "count": total,
    }


@router.get("/{assessment_id}")
def get_assessment_detail(
    session: SessionDep,
    current_user: CurrentUser,
    assessment_id: uuid.UUID,
) -> Any:
    """Get a specific assessment by ID."""
    assessment = get_assessment(session=session, assessment_id=assessment_id)
    if not assessment or assessment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Assessment not found")
    try:
        results = json.loads(assessment.results_json)
    except (json.JSONDecodeError, TypeError):
        results = None

    return {
        "id": str(assessment.id),
        "postcode": assessment.postcode,
        "overall_rating": assessment.overall_rating,
        "created_at": assessment.created_at,
        "results": results,
    }
