"""ResourceESGAgent - Universal SQLAlchemy models for timber/amber/ore ESG tracking."""
import uuid
from datetime import date
from sqlalchemy import Column, Date, ForeignKey, Numeric, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

RESOURCE_TYPES = ("timber", "amber", "ore", "coal", "gas", "rare_earth")
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class ResourceEnterprise(Base):
    """Legal entity that produces or ships natural resources."""
    __tablename__ = "resource_enterprises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edrpou = Column(Text, unique=True, nullable=False, index=True)
    name = Column(Text)
    region = Column(Text)  # Chernihiv, Rivne, Zhytomyr...
    resource_type = Column(SAEnum(*RESOURCE_TYPES, name="resource_type_enum"))
    license_number = Column(Text)
    license_valid_until = Column(Date)
    is_active = Column(Text, default="true")

    shipments = relationship("ResourceShipment", back_populates="enterprise")
    risk_profiles = relationship("EsgResourceRiskProfile", back_populates="enterprise")


class ResourceShipment(Base):
    """Single shipment of a natural resource — core detection unit."""
    __tablename__ = "resource_shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("resource_enterprises.id"), index=True)
    resource_type = Column(SAEnum(*RESOURCE_TYPES, name="resource_type_enum"), nullable=False)
    date = Column(Date, nullable=False)
    origin_station = Column(Text)    # Railway station or warehouse
    destination = Column(Text)       # e.g. "PL-Medika", "SK-Krakow"
    declared_type = Column(Text)     # What the shipper claims: "firewood", "scrap"
    estimated_type = Column(Text)    # What ESG engine estimates: "roundwood", "raw_amber"
    volume_kg = Column(Numeric)      # Weight in kg (or m3 stored as kg for timber)
    buyer_legal_entity = Column(Text)
    risk_flags = Column(ARRAY(Text), default=[])
    # timber_hack | amber_hack | ore_hack | export_limit_exceeded | critical_species

    enterprise = relationship("ResourceEnterprise", back_populates="shipments")


class EsgResourceRiskProfile(Base):
    """Aggregated ESG risk score per enterprise per reporting period."""
    __tablename__ = "esg_resource_risk_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("resource_enterprises.id"), index=True)
    resource_type = Column(SAEnum(*RESOURCE_TYPES, name="resource_type_enum"))
    period = Column(Text, nullable=False)   # "2025-Q4", "2025-10"
    risk_level = Column(SAEnum(*RISK_LEVELS, name="risk_level_enum"), default="LOW")
    total_shipments = Column(Numeric, default=0)
    flagged_shipments = Column(Numeric, default=0)
    total_volume_kg = Column(Numeric, default=0)
    flagged_volume_kg = Column(Numeric, default=0)
    hack_count = Column(Numeric, default=0)
    export_limit_exceeded = Column(Numeric, default=0)
    critical_species_count = Column(Numeric, default=0)
    narrative = Column(Text)   # LLM-generated audit narrative
    generated_at = Column(Date)

    enterprise = relationship("ResourceEnterprise", back_populates="risk_profiles")


class ResourceAlert(Base):
    """Real-time alert triggered by ESG rule violation."""
    __tablename__ = "resource_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("resource_shipments.id"))
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("resource_enterprises.id"))
    alert_type = Column(Text)   # "hack_detected", "export_limit", "critical_species"
    severity = Column(SAEnum(*RISK_LEVELS, name="risk_level_enum"))
    message = Column(Text)
    triggered_at = Column(Date)
    acknowledged = Column(Text, default="false")
    channel = Column(Text, default="telegram")  # telegram | email | nats | webhook
