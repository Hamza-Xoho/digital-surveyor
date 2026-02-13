import uuid
from typing import Any

from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    postcode: str = Field(
        ..., pattern=r"^[A-Za-z]{1,2}\d[A-Za-z\d]?\s*\d[A-Za-z]{2}$"
    )
    vehicle_classes: list[str] | None = None


class VehicleCheck(BaseModel):
    name: str
    rating: str  # "GREEN" | "AMBER" | "RED"
    detail: str
    value: float | None = None
    threshold: float | None = None


class VehicleAssessmentResult(BaseModel):
    vehicle_name: str
    vehicle_class: str
    overall_rating: str  # "GREEN" | "AMBER" | "RED"
    checks: list[VehicleCheck]
    recommendation: str


class WidthAnalysis(BaseModel):
    min_width_m: float
    max_width_m: float
    mean_width_m: float
    pinch_points: list[dict[str, Any]] = []
    measurement_lines_geojson: dict[str, Any] | None = None


class GradientAnalysis(BaseModel):
    max_gradient_pct: float
    mean_gradient_pct: float
    steep_segments: list[dict[str, Any]] = []
    profile_geojson: dict[str, Any] | None = None


class AssessmentResponse(BaseModel):
    id: uuid.UUID | None = None
    postcode: str
    latitude: float
    longitude: float
    easting: float
    northing: float
    overall_rating: str
    vehicle_assessments: list[VehicleAssessmentResult]
    width_analysis: WidthAnalysis | None = None
    gradient_analysis: GradientAnalysis | None = None
    geojson_overlays: dict[str, Any] = {}


class AssessmentList(BaseModel):
    data: list[AssessmentResponse]
    count: int
