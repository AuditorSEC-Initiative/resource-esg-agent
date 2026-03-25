"""Unit tests for ResourceESGAgent API and service layer."""
import os
import sys
import pytest
from datetime import datetime

# Use SQLite for tests (no PostgreSQL needed)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_esg.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agents.resource_esg.models import Base, ResourceShipment
from agents.resource_esg.api import app, get_db
from agents.resource_esg.service import classify_shipment, RESOURCE_RULES

TEST_DB_URL = "sqlite:///./test_esg.db"


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def client(db_engine):
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Service layer tests ---

def test_resource_rules_defined():
    """RESOURCE_RULES must have timber, amber, ore."""
    assert "timber" in RESOURCE_RULES
    assert "amber" in RESOURCE_RULES
    assert "ore" in RESOURCE_RULES


def test_classify_timber_hack():
    """Roundwood shipped as firewood should be flagged."""
    result = classify_shipment(
        resource_type="timber",
        declared_category="firewood",
        volume_m3=2.0,
        weight_kg=1500,
        species="бук",
    )
    assert result["hack_detected"] is True
    assert result["risk_level"] in ("HIGH", "CRITICAL")


def test_classify_timber_normal():
    """Legitimate firewood with low volume should not be flagged."""
    result = classify_shipment(
        resource_type="timber",
        declared_category="firewood",
        volume_m3=0.5,
        weight_kg=200,
        species="береза",
    )
    assert result["hack_detected"] is False
    assert result["risk_level"] in ("LOW", "MEDIUM")


def test_classify_amber_scrap_hack():
    """Raw amber shipped as scrap should be flagged."""
    result = classify_shipment(
        resource_type="amber",
        declared_category="scrap",
        volume_m3=0,
        weight_kg=500,
    )
    assert result["hack_detected"] is True


def test_classify_ore_normal():
    """Standard ore shipment without hack pattern."""
    result = classify_shipment(
        resource_type="ore",
        declared_category="iron_ore",
        volume_m3=0,
        weight_kg=2000,
    )
    assert result["risk_level"] is not None


# --- API endpoint tests ---

def test_health_endpoint(client):
    """Health check must return 200."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_post_shipment(client):
    """POST /api/v1/esg/resource/shipments must accept valid shipment."""
    payload = {
        "enterprise_id": "ENT-TEST-001",
        "resource_type": "timber",
        "declared_category": "firewood",
        "volume_m3": 2.0,
        "weight_kg": 1500.0,
        "species": "бук",
        "origin_region": "Zhytomyr",
        "shipment_date": datetime.utcnow().isoformat(),
        "period": "2026-03",
    }
    resp = client.post("/api/v1/esg/resource/shipments", json=payload)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert "risk_level" in data or "id" in data


def test_get_shipments(client):
    """GET /api/v1/esg/resource/all/shipments must return list."""
    resp = client.get("/api/v1/esg/resource/all/shipments")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_esg_profile(client):
    """GET /api/v1/esg/resource/{enterprise_id}/{period} must return profile."""
    resp = client.get("/api/v1/esg/resource/ENT-TEST-001/2026-03")
    assert resp.status_code == 200
    data = resp.json()
    assert "enterprise_id" in data or "risk_level" in data or "shipments" in data
