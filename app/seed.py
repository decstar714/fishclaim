import os

from app.database import SessionLocal, Base, engine
from app import models
from app.auth import get_password_hash


DEFAULT_USER_EMAIL = os.getenv("SEED_USER_EMAIL", "owner@example.com")
DEFAULT_USER_USERNAME = os.getenv("SEED_USER_USERNAME", "owner")
DEFAULT_USER_DISPLAY_NAME = os.getenv("SEED_USER_DISPLAY_NAME", "FishClaim Owner")
DEFAULT_USER_PASSWORD = os.getenv("SEED_USER_PASSWORD", "ChangeMe!123")
FORCE_RESET = os.getenv("SEED_FORCE_RESET", "true").lower() in {"1", "true", "yes"}

def main():
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    user = seed_user(db)
    water = seed_water(db)
    seed_zones(db, water)
    seed_species(db)

    db.commit()
    db.close()
    print("✅ Seed complete!")


def seed_user(db):
    existing = (
        db.query(models.User)
        .filter_by(username=DEFAULT_USER_USERNAME)
        .one_or_none()
    )

    if existing:
        if FORCE_RESET:
            print(f"Resetting password for user '{DEFAULT_USER_USERNAME}'...")
            existing.email = DEFAULT_USER_EMAIL
            existing.display_name = DEFAULT_USER_DISPLAY_NAME
            existing.password_hash = get_password_hash(DEFAULT_USER_PASSWORD)
        else:
            print(f"User '{DEFAULT_USER_USERNAME}' already exists; leaving as-is.")
        return existing

    print("Seeding user...")
    user = models.User(
        email=DEFAULT_USER_EMAIL,
        username=DEFAULT_USER_USERNAME,
        password_hash=get_password_hash(DEFAULT_USER_PASSWORD),
        display_name=DEFAULT_USER_DISPLAY_NAME,
    )
    db.add(user)
    db.flush()
    return user


def seed_water(db):
    water = (
        db.query(models.Water)
        .filter_by(name="South Branch Raritan River")
        .one_or_none()
    )
    if water:
        print("Water already exists; leaving as-is.")
        return water

    print("Seeding water...")
    water = models.Water(
        name="South Branch Raritan River",
        type="river",
        region="NJ",
        description="Home water",
    )
    db.add(water)
    db.flush()
    return water


def seed_zones(db, water: models.Water):
    zone_specs = [
        (
            "Ken Lockwood Gorge",
            "TCA gorge section",
            1,
        ),
        (
            "Califon to Cokesbury",
            "Downstream section",
            2,
        ),
    ]
    for name, description, order_index in zone_specs:
        zone = (
            db.query(models.Zone)
            .filter_by(water_id=water.id, name=name)
            .one_or_none()
        )
        if zone:
            continue
        print(f"Seeding zone '{name}'...")
        db.add(
            models.Zone(
                water_id=water.id,
                name=name,
                description=description,
                order_index=order_index,
            )
        )


def seed_species(db):
    species_specs = [
        ("Brown Trout", "Salmo trutta", "trout"),
        ("Rainbow Trout", "Oncorhynchus mykiss", "trout"),
    ]
    for common_name, scientific_name, category in species_specs:
        species = (
            db.query(models.Species)
            .filter_by(common_name=common_name)
            .one_or_none()
        )
        if species:
            continue
        print(f"Seeding species '{common_name}'...")
        db.add(
            models.Species(
                common_name=common_name,
                scientific_name=scientific_name,
                category=category,
            )
        )


if __name__ == "__main__":
    main()
