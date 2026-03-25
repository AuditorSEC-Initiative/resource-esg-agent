"""ResourceESGAgent - Universal rules engine for ESG risk classification."""
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import ResourceShipment, EsgResourceRiskProfile, ResourceAlert

# ============================================================
# RESOURCE_RULES: pluggable config — add new resource types here
# ============================================================
RESOURCE_RULES = {
    "timber": {
        "hack_patterns": {
            "firewood": [(1.8, 2.6, "roundwood")],       # m3 range that suggests roundwood
            "waste_wood": [(0.5, 1.5, "processed_timber")],
        },
        "critical_species": {"бук", "модрина", "oak", "beech", "larch"},
        "export_limit_m3": None,  # no national limit but check license
    },
    "amber": {
        "hack_patterns": {
            "scrap": [(0.1, 50.0, "raw_amber")],
            "mineral_waste": [(5.0, 200.0, "semi_processed_amber")],
        },
        "critical_species": {"балтийський", "blue_earth", "succinite"},
        "export_limit_kg": 1000,  # Ukraine customs threshold
    },
    "ore": {
        "hack_patterns": {
            "construction_sand": [(1000, 5000, "strategic_ore")],
            "gravel": [(500, 3000, "titanium_ore")],
        },
        "critical_species": {"titanium", "lithium", "rare_earth", "uranium"},
        "export_limit_kg": 10000,
    },
    "coal": {
        "hack_patterns": {
            "charcoal": [(100, 2000, "coking_coal")],
        },
        "critical_species": {"anthracite"},
        "export_limit_kg": None,
    },
}


def classify_shipment(sh: ResourceShipment) -> ResourceShipment:
    """Apply RESOURCE_RULES to a shipment and populate risk_flags."""
    rules = RESOURCE_RULES.get(sh.resource_type, {})
    hack_patterns = rules.get("hack_patterns", {})
    export_limit = rules.get("export_limit_kg") or rules.get("export_limit_m3")
    critical_species = rules.get("critical_species", set())

    flags = list(sh.risk_flags or [])

    # 1. Hack pattern detection
    if sh.declared_type and sh.declared_type in hack_patterns:
        for min_vol, max_vol, estimated in hack_patterns[sh.declared_type]:
            vol = float(sh.volume_kg or 0)
            if min_vol <= vol <= max_vol:
                flag = f"{sh.resource_type}_hack"
                if flag not in flags:
                    flags.append(flag)
                sh.estimated_type = estimated
                break

    # 2. Export limit check
    if export_limit and sh.volume_kg and float(sh.volume_kg) > export_limit:
        if "export_limit_exceeded" not in flags:
            flags.append("export_limit_exceeded")

    # 3. Critical species / material check
    declared_lower = (sh.declared_type or "").lower()
    for species in critical_species:
        if species.lower() in declared_lower:
            if "critical_species" not in flags:
                flags.append("critical_species")
            break

    sh.risk_flags = list(set(flags))
    return sh


def compute_risk_level(flagged_ratio: float, hack_count: int, export_violations: int) -> str:
    """Determine enterprise ESG risk level from aggregated stats."""
    if hack_count >= 5 or export_violations >= 3 or flagged_ratio >= 0.5:
        return "CRITICAL"
    elif hack_count >= 2 or export_violations >= 1 or flagged_ratio >= 0.2:
        return "HIGH"
    elif hack_count >= 1 or flagged_ratio >= 0.05:
        return "MEDIUM"
    return "LOW"


def aggregate_enterprise_profile(
    enterprise_id: str,
    period: str,
    resource_type: str,
    db: Session
) -> EsgResourceRiskProfile:
    """Compute or refresh ESG risk profile for an enterprise."""
    from datetime import date

    shipments: List[ResourceShipment] = (
        db.query(ResourceShipment)
        .filter(
            ResourceShipment.enterprise_id == enterprise_id,
            ResourceShipment.resource_type == resource_type,
        )
        .all()
    )

    total = len(shipments)
    flagged = [s for s in shipments if s.risk_flags]
    hacks = [s for s in shipments if any("hack" in f for f in (s.risk_flags or []))]
    export_viol = [s for s in shipments if "export_limit_exceeded" in (s.risk_flags or [])]
    total_vol = sum(float(s.volume_kg or 0) for s in shipments)
    flagged_vol = sum(float(s.volume_kg or 0) for s in flagged)

    ratio = len(flagged) / total if total > 0 else 0.0
    risk_level = compute_risk_level(ratio, len(hacks), len(export_viol))

    profile = db.query(EsgResourceRiskProfile).filter_by(
        enterprise_id=enterprise_id, period=period, resource_type=resource_type
    ).first()

    if not profile:
        profile = EsgResourceRiskProfile(
            enterprise_id=enterprise_id,
            period=period,
            resource_type=resource_type,
        )
        db.add(profile)

    profile.risk_level = risk_level
    profile.total_shipments = total
    profile.flagged_shipments = len(flagged)
    profile.total_volume_kg = total_vol
    profile.flagged_volume_kg = flagged_vol
    profile.hack_count = len(hacks)
    profile.export_limit_exceeded = len(export_viol)
    profile.generated_at = date.today()
    db.commit()
    db.refresh(profile)
    return profile


def generate_alerts(shipment: ResourceShipment, db: Session) -> List[ResourceAlert]:
    """Create ResourceAlert records for each risk flag on a shipment."""
    from datetime import date
    alerts = []
    severity_map = {
        "timber_hack": "HIGH",
        "amber_hack": "CRITICAL",
        "ore_hack": "CRITICAL",
        "export_limit_exceeded": "HIGH",
        "critical_species": "MEDIUM",
    }
    for flag in (shipment.risk_flags or []):
        alert = ResourceAlert(
            shipment_id=shipment.id,
            enterprise_id=shipment.enterprise_id,
            alert_type=flag,
            severity=severity_map.get(flag, "MEDIUM"),
            message=(
                f"[{shipment.resource_type.upper()}] {flag} detected: "
                f"declared={shipment.declared_type}, estimated={shipment.estimated_type}, "
                f"volume={shipment.volume_kg}kg, dest={shipment.destination}"
            ),
            triggered_at=date.today(),
            channel="telegram",
        )
        db.add(alert)
        alerts.append(alert)
    if alerts:
        db.commit()
    return alerts
