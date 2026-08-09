from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    Index,
    Text,
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

    # A zone is a stretch of river, so its geometry is a line, not an area.
    # USGS has already segmented every stream in the country: `comid` is the
    # NHDPlus identifier for this reach, and `geometry_geojson` is the LineString
    # it hands back. Stored as text rather than a PostGIS column on purpose --
    # the map only needs to draw it, and nothing here does spatial queries yet.
    # The day something needs "which reach contains this point", that is the
    # moment PostGIS earns its place, not before.
    comid = Column(String, index=True)
    geometry_geojson = Column(Text)

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

    # One ACTIVE claim per (zone, species) -- enforced as a PARTIAL unique index.
    #
    # This was previously a plain UniqueConstraint on (zone_id, species_id,
    # is_active), which is subtly wrong: it also constrains the *inactive* rows
    # to one per zone+species. Beaten and expired claims are kept as history with
    # is_active=False, so the second time a claim was superseded there were two
    # rows wanting (zone, species, False) and the insert died with an
    # IntegrityError. In practice the game broke on the THIRD time a claim
    # changed hands in any zone+species pair -- which is the core loop.
    #
    # A partial index constrains only the rows that matter: at most one row with
    # is_active true, and unlimited history beneath it.
    __table_args__ = (
        Index(
            "uq_active_claim_per_zone_species",
            "zone_id", "species_id",
            unique=True,
            postgresql_where=Column("is_active") == True,   # noqa: E712
            sqlite_where=Column("is_active") == True,       # noqa: E712
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
