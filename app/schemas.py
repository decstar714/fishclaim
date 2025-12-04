from datetime import datetime
from pydantic import BaseModel


class WaterBase(BaseModel):
    name: str
    type: str | None = "river"
    region: str | None = None
    description: str | None = None


class Water(WaterBase):
    id: int

    class Config:
        from_attributes = True


class ZoneBase(BaseModel):
    name: str
    description: str | None = None
    order_index: int | None = 0


class Zone(ZoneBase):
    id: int
    water_id: int

    class Config:
        from_attributes = True


class CatchCreate(BaseModel):
    water_id: int
    zone_id: int
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
    water_id: int
    zone_id: int
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
    user_id: int
    zone_id: int
    species_id: int
    length_cm: float
    created_at: datetime
    expires_at: datetime | None = None

    class Config:
        from_attributes = True

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


class SessionBase(BaseModel):
    water_id: int
    zone_id: int
    species_id: int | None = None
    started_at: datetime | None = None
    duration_minutes: int | None = None
    method: str | None = None
    notes: str | None = None
    conditions: str | None = None
    best_length_cm: float | None = None


class Session(SessionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SessionCreate(SessionBase):
    pass
