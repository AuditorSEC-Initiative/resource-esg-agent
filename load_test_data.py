"""Load multi_resource.csv test data into ResourceESGAgent database."""
import csv
import os
import sys
from datetime import datetime

# Allow running from repo root
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agents.resource_esg.models import Base, ResourceShipment

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_test.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "tests", "multi_resource.csv")


def load():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    loaded = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            shipment = ResourceShipment(
                enterprise_id=row.get("enterprise_id", "UNKNOWN"),
                resource_type=row.get("resource_type", "timber"),
                declared_category=row.get("declared_category", ""),
                volume_m3=float(row.get("volume_m3", 0)),
                weight_kg=float(row.get("weight_kg", 0)),
                species=row.get("species", None),
                origin_region=row.get("origin_region", None),
                shipment_date=datetime.fromisoformat(
                    row["shipment_date"]
                ) if row.get("shipment_date") else datetime.utcnow(),
                period=row.get("period", datetime.utcnow().strftime("%Y-%m")),
            )
            session.add(shipment)
            loaded += 1

    session.commit()
    session.close()
    print(f"[load_test_data] Loaded {loaded} shipments from {CSV_PATH}")


if __name__ == "__main__":
    load()
