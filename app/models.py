from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    catches = relationship("Catch", back_populates="user")
    claims = relationship("Claim", back_populates="user")


class Water(Base):
    __tablename__ = "waters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, default="river")
    region = Column(String)
    description = Column(String)

    zones = relationship("Zone", back_populates="water")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    water_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    order_index = Column(Integer, default=0)

    water = relationship("Water", back_populates="zones")
    catches = relationship("Catch", back_populates="zone")
    claims = relationship("Claim", back_populates="zone")


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
    water_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
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
    zone = relationship("Zone", back_populates="catches")
    species = relationship("Species", back_populates="catches")
    water = relationship("Water")
    claim = relationship("Claim", back_populates="catch", uselist=False)


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    water_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=False)

    length_cm = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime)

    user = relationship("User", back_populates="claims")
    zone = relationship("Zone", back_populates="claims")
    species = relationship("Species", back_populates="claims")
    catch = relationship("Catch", back_populates="claim")
    water = relationship("Water")

    __table_args__ = (
        UniqueConstraint(
            "zone_id", "species_id", "is_active",
            name="uq_active_claim_per_zone_species",
        ),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    water_id = Column(Integer, ForeignKey("waters.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer)
    method = Column(String)
    notes = Column(String)
    conditions = Column(String)
    best_length_cm = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    water = relationship("Water")
    zone = relationship("Zone")
    species = relationship("Species")
