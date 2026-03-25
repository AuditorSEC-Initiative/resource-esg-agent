"""ResourceESGAgent - FastAPI REST API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from .models import ResourceShipment, EsgResourceRiskProfile, ResourceEnterprise
from .service import classify_shipment, aggregate_enterprise_profile, generate_alerts

router = APIRouter(prefix="/api/v1/esg/resource", tags=["ResourceESG"])

# Prometheus metrics
PROFILES_TOTAL = Counter(
    "resource_esg_profiles_total",
    "ESG profiles computed",
    ["resource_type", "level"]
)
HACK_DETECTED = Counter(
    "resource_hack_shipments_detected",
    "Hack pattern detections",
    ["resource_type"]
)


# --- Pydantic schemas ---

class ShipmentIn(BaseModel):
    enterprise_edrpou: str
    resource_type: str
    date: str
    origin_station: Optional[str] = None
    destination: Optional[str] = None
    declared_type: Optional[str] = None
    volume_kg: Optional[float] = None
    buyer_legal_entity: Optional[str] = None


class ShipmentOut(BaseModel):
    id: str
    resource_type: str
    date: str
    declared_type: Optional[str]
    estimated_type: Optional[str]
    volume_kg: Optional[float]
    risk_flags: List[str]
    destination: Optional[str]

    class Config:
        from_attributes = True


class ProfileOut(BaseModel):
    enterprise_id: str
    resource_type: str
    period: str
    risk_level: str
    total_shipments: int
    flagged_shipments: int
    hack_count: int
    export_limit_exceeded: int
    narrative: Optional[str]

    class Config:
        from_attributes = True


# --- Dependency ---

def get_db():
    """FastAPI dependency: yields SQLAlchemy Session. Override in production."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    engine = create_engine(os.getenv("DATABASE_URL", "postgresql://localhost/resource_esg"))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Endpoints ---

@router.post("/shipments", response_model=ShipmentOut)
def ingest_shipment(
    payload: ShipmentIn,
    db: Session = Depends(get_db)
):
    """Ingest a new resource shipment, classify it, and create alerts."""
    enterprise = db.query(ResourceEnterprise).filter_by(
        edrpou=payload.enterprise_edrpou
    ).first()
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise not found")

    from datetime import date as date_cls
    sh = ResourceShipment(
        enterprise_id=enterprise.id,
        resource_type=payload.resource_type,
        date=date_cls.fromisoformat(payload.date),
        origin_station=payload.origin_station,
        destination=payload.destination,
        declared_type=payload.declared_type,
        volume_kg=payload.volume_kg,
        buyer_legal_entity=payload.buyer_legal_entity,
        risk_flags=[],
    )
    sh = classify_shipment(sh)
    db.add(sh)
    db.commit()
    db.refresh(sh)

    # Metrics
    for flag in sh.risk_flags:
        if "hack" in flag:
            HACK_DETECTED.labels(resource_type=sh.resource_type).inc()

    generate_alerts(sh, db)
    return sh


@router.get("/{enterprise_id}/shipments", response_model=List[ShipmentOut])
def get_shipments(
    enterprise_id: str,
    resource_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List shipments for an enterprise, optionally filtered by resource_type."""
    q = db.query(ResourceShipment).filter(
        ResourceShipment.enterprise_id == enterprise_id
    )
    if resource_type:
        q = q.filter(ResourceShipment.resource_type == resource_type)
    return q.order_by(ResourceShipment.date.desc()).all()


@router.get("/{enterprise_id}/{period}", response_model=ProfileOut)
def get_profile(
    enterprise_id: str,
    period: str,
    resource_type: str = Query("timber"),
    refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get ESG risk profile. Set refresh=true to recompute."""
    if refresh:
        profile = aggregate_enterprise_profile(enterprise_id, period, resource_type, db)
    else:
        profile = db.query(EsgResourceRiskProfile).filter_by(
            enterprise_id=enterprise_id,
            period=period,
            resource_type=resource_type
        ).first()
        if not profile:
            profile = aggregate_enterprise_profile(enterprise_id, period, resource_type, db)

    PROFILES_TOTAL.labels(
        resource_type=resource_type,
        level=profile.risk_level
    ).inc()
    return profile


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# --- App factory ---

def create_app():
    from fastapi import FastAPI
    app = FastAPI(
        title="ResourceESGAgent API",
        description="Universal ESG risk detection: timber/amber/ore. Part of AuditorSEC.",
        version="1.0.0",
    )
    app.include_router(router)
    return app


app = create_app()
