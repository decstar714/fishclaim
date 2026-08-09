from app import models
from app.core.database import SessionLocal, Base, engine

def main():
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Check if we already seeded
    existing = db.query(models.User).filter_by(username="conor").first()
    if existing:
        print("Seed data already exists, skipping.")
        db.close()
        return

    print("Seeding user...")
    user = models.User(
        email="test@example.com",
        username="conor",
        password_hash="dev-only-placeholder",
        display_name="Conor Dev",
    )
    db.add(user)
    db.flush()  # get user.id

    print("Seeding water...")
    water = models.WaterBody(
        name="South Branch Raritan River",
        region="NJ",
        description="Home water",
    )
    db.add(water)
    db.flush()

    print("Seeding zones...")
    reach = models.Reach(
        water_body_id=water.id,
        name="Ken Lockwood Gorge",
        description="TCA gorge section",
        order_index=1,
    )
    db.add(reach)

    print("Seeding species...")
    species = [
        models.Species(
            common_name="Brown Trout",
            scientific_name="Salmo trutta",
            category="trout",
        ),
        models.Species(
            common_name="Rainbow Trout",
            scientific_name="Oncorhynchus mykiss",
            category="trout",
        ),
    ]
    db.add_all(species)

    db.commit()
    db.close()
    print("✅ Seed complete!")


if __name__ == "__main__":
    main()
