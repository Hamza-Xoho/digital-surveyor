from typing import Any

from pydantic import BaseModel


class Coordinate(BaseModel):
    latitude: float
    longitude: float
    easting: float
    northing: float


class BoundingBox(BaseModel):
    min_easting: float
    min_northing: float
    max_easting: float
    max_northing: float

    @classmethod
    def from_centre(cls, easting: float, northing: float, radius: int = 200) -> "BoundingBox":
        return cls(
            min_easting=easting - radius,
            min_northing=northing - radius,
            max_easting=easting + radius,
            max_northing=northing + radius,
        )

    def to_wfs_bbox(self) -> str:
        return (
            f"{self.min_easting},{self.min_northing},"
            f"{self.max_easting},{self.max_northing},EPSG:27700"
        )


class GeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: list[dict[str, Any]] = []
    feature_count: int = 0
