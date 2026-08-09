from datetime import datetime
from enum import Enum
from typing import Optional

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, field_serializer


class GeometryMixin(BaseModel):
    geometry: Optional[str] = None

    @field_serializer("geometry")
    def serialize_geometry(self, value):
        if value is None:
            return None
        try:
            return to_shape(value).wkt
        except Exception:
            return str(value)


class WaterBodyBase(GeometryMixin):
    name: str
    region: str | None = None
    description: str | None = None


class WaterBodyRead(WaterBodyBase):
    id: int

    class Config:
        from_attributes = True


class ReachBase(GeometryMixin):
    name: str
    description: str | None = None
    order_index: int | None = 0
    water_body_id: int


class ReachRead(ReachBase):
    id: int

    class Config:
        from_attributes = True


class CatchCreate(BaseModel):
    water_body_id: int
    reach_id: int
    species_id: int
    length_cm: float
    weight_kg: float | None = None
    method: str | None = None
    notes: str | None = None
    lat: float | None = None
    lng: float | None = None


class Catch(BaseModel):
    id: int
    user_id: int
    water_body_id: int
    reach_id: int
    species_id: int
    length_cm: float
    weight_kg: float | None
    method: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class Claim(BaseModel):
    id: int
    user_id: str
    reach_id: int
    species_id: int | None = None
    length_cm: float
    status: str
    created_at: datetime
    expires_at: datetime | None = None
    note: str | None = None

    class Config:
        from_attributes = True


class ClaimCreate(BaseModel):
    reach_id: int
    note: str | None = None
    ttl_hours: int | None = None


class UserBase(BaseModel):
    email: str
    username: str
    display_name: str | None = None


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    username: str
    display_name: str | None = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
