from datetime import datetime, timedelta
from enum import Enum

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClaimStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    catches = relationship("Catch", back_populates="user")


class WaterBody(Base):
    __tablename__ = "waters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    region = Column(String)
    description = Column(String)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)

    reaches = relationship("Reach", back_populates="water_body")


class Reach(Base):
    __tablename__ = "reaches"

    id = Column(Integer, primary_key=True, index=True)
    water_body_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    order_index = Column(Integer, default=0)

    water_body = relationship("WaterBody", back_populates="reaches")
    catches = relationship("Catch", back_populates="reach")
    claims = relationship("Claim", back_populates="reach")


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    common_name = Column(String, nullable=False, unique=True)
    scientific_name = Column(String)
    category = Column(String)

    catches = relationship("Catch", back_populates="species")
    claims = relationship("Claim", back_populates="species")


class Catch(Base):
    __tablename__ = "catches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    water_body_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    reach_id = Column(Integer, ForeignKey("reaches.id"), nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)

    length_cm = Column(Float, nullable=False)
    weight_kg = Column(Float)
    photo_url = Column(String)

    lat = Column(Float)
    lng = Column(Float)

    method = Column(String)
    notes = Column(String)

    caught_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="catches")
    reach = relationship("Reach", back_populates="catches")
    species = relationship("Species", back_populates="catches")
    water_body = relationship("WaterBody")
    claim = relationship("Claim", back_populates="catch", uselist=False)


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    water_body_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    reach_id = Column(Integer, ForeignKey("reaches.id"), nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=True)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=True)

    length_cm = Column(Float, nullable=False, default=0.0)
    status = Column(String, default=ClaimStatus.ACTIVE.value, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=72))
    note = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime)

    reach = relationship("Reach", back_populates="claims")
    species = relationship("Species", back_populates="claims")
    catch = relationship("Catch", back_populates="claim")
    water_body = relationship("WaterBody")

    __table_args__ = ()
