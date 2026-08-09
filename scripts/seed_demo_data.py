#!/usr/bin/env python
"""
Seed demo waters/reaches with simple geometries for map/claim testing.

Usage:
  source .venv/bin/activate
  python scripts/seed_demo_data.py
"""

import os
from typing import List

from geoalchemy2.shape import from_shape
from shapely.geometry import box

from app import models
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db, engine


def make_reach_geoms() -> List:
    # Create 3 simple rectangles near a fixed bbox (adjust as needed)
    base_lon, base_lat = -74.742, 40.612
    width = 0.01
    height = 0.01
    boxes = []
    for i in range(3):
        lon0 = base_lon + i * width * 1.5
        lat0 = base_lat
        b = box(lon0, lat0, lon0 + width, lat0 + height)
        boxes.append(b)
    return boxes


def seed_demo(reset: bool = False):
    init_db()
    with SessionLocal() as db:
        demo_water = (
            db.query(models.WaterBody).filter(models.WaterBody.name == "Demo Creek").first()
        )
        if reset and demo_water:
            db.query(models.Reach).filter(models.Reach.water_body_id == demo_water.id).delete()
            db.delete(demo_water)
            db.commit()
            demo_water = None

        if demo_water:
            print("Demo data already present; skipping (use --reset to recreate).")
            return

        demo_water = models.WaterBody(name="Demo Creek", region="Demo Region", description="Demo seeded water")
        db.add(demo_water)
        db.flush()

        reaches = []
        geoms = make_reach_geoms()
        for idx, geom in enumerate(geoms, start=1):
            reach = models.Reach(
                water_body_id=demo_water.id,
                name=f"Reach {idx}",
                description=f"Demo reach {idx}",
                order_index=idx,
                geometry=from_shape(geom, srid=4326) if engine.url.get_backend_name() == "postgresql" else None,
            )
            reaches.append(reach)
        db.add_all(reaches)
        db.commit()
        print(f"Seeded {demo_water.name} with {len(reaches)} reaches.")


if __name__ == "__main__":
    reset = "--reset-demo" in os.sys.argv
    seed_demo(reset=reset)
