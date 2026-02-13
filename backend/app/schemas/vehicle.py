import uuid

from pydantic import BaseModel


class VehicleProfileCreate(BaseModel):
    name: str
    vehicle_class: str
    width_m: float
    length_m: float
    height_m: float
    weight_kg: int
    turning_radius_m: float
    mirror_width_m: float = 0.25


class VehicleProfileRead(VehicleProfileCreate):
    id: uuid.UUID

    class Config:
        from_attributes = True


class VehicleProfileList(BaseModel):
    data: list[VehicleProfileRead]
    count: int
