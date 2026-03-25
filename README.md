# ResourceESGAgent

[![CI](https://github.com/AuditorSEC-Initiative/resource-esg-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/AuditorSEC-Initiative/resource-esg-agent/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ukraine](https://img.shields.io/badge/Made%20in-Ukraine-blue)](https://github.com/AuditorSEC-Initiative)

**Universal ESG risk detection agent** for natural resources: timber 🌲, amber 💎, ore ⛏️ — and extensible to any resource type.

Part of the [AuditorSEC Initiative](https://github.com/AuditorSEC-Initiative) ecosystem. Implements the **UHIP-2A Resource Integrity** module for reconstruction risk analytics.

---

## 🎯 What It Does

- **Hack pattern detection**: identifies misclassified shipments (e.g. roundwood smuggled as "firewood", raw amber as "scrap")
- **Multi-resource rules engine**: pluggable `RESOURCE_RULES` config per resource type
- **ESG risk profiling**: per-enterprise risk scores (LOW / MEDIUM / HIGH / CRITICAL)
- **React dashboard**: maps, pie charts, shipment tables, PDF export
- **Grafana integration**: real-time Prometheus metrics for all resource types
- **n8n workflow**: YouTube/RSS → LLM summaries → NATS events → ESG agent

---

## 🏗️ Architecture

```
agents/resource_esg/
├── models.py          # SQLAlchemy: ResourceShipment, EsgResourceRiskProfile
├── service.py         # RESOURCE_RULES engine + classify_shipment()
├── api.py             # FastAPI endpoints
├── ui/                # React dashboard (maps, charts, reports)
├── grafana/           # Grafana dashboard.json (multi-resource metrics)
├── k8s/               # Helm charts for Kubernetes deployment
├── tests/
│   └── multi_resource.csv   # Test data: timber/amber/ore
├── deploy.sh          # One-command production deploy
└── README.md
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/AuditorSEC-Initiative/resource-esg-agent
cd resource-esg-agent

# Install backend deps
pip install fastapi sqlalchemy psycopg2-binary uvicorn

# Start API
uvicorn agents.resource_esg.api:app --reload

# Load test data
python load_test_data.py

# Or full production deploy
bash deploy.sh
```

---

## 📦 Resource Rules

```python
RESOURCE_RULES = {
    "timber": {
        "hack_patterns": {"firewood": [(1.8, 2.6, "roundwood")]},
        "critical_species": {"бук", "модрина"}
    },
    "amber": {
        "hack_patterns": {"scrap": [(0.1, 50, "raw_amber")]},
        "export_limit_kg": 1000
    },
    "ore": {
        "hack_patterns": {"construction_sand": [(1000, 5000, "strategic_ore")]},
        "critical_species": {"titanium", "lithium"}
    }
}
```

Add new resource types by extending `RESOURCE_RULES` — no code changes needed.

---

## 🖥️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/esg/resource/{enterprise_id}/{period}` | ESG risk profile |
| GET | `/api/v1/esg/resource/{enterprise_id}/shipments` | Shipment list (filterable by resource_type) |
| POST | `/api/v1/esg/resource/shipments` | Ingest new shipment |
| GET | `/api/v1/esg/resource/metrics` | Prometheus metrics |

---

## 📊 Grafana Dashboard

Import `grafana/dashboard.json` into your Grafana instance.

Panels:
- **Risks by Resource Type** — pie/bar per timber/amber/ore
- **Hack Detection Rate** — time series over 24h
- **Enterprise Risk Heatmap**
- **Variable filter**: `resource_type` (multi-select)

---

## 🔗 Ecosystem Integration

```
YouTube RSS → summaries-fuel LLM →
  if "ліс|янтарь|деревина" detected →
    NATS event: resource_shipment.created →
      ResourceESGAgent → ESG profile → alert → PDF report
```

Connects to:
- [`auditorsec-summaries-fuel-mvp`](https://github.com/AuditorSEC-Initiative/auditorsec-summaries-fuel-mvp) — LLM narrative pipeline
- [`auditorsec-llm-bridge`](https://github.com/AuditorSEC-Initiative/auditorsec-llm-bridge) — AI audit reasoning
- [`bachmach-pqc-iot-sentinel`](https://github.com/AuditorSEC-Initiative/bachmach-pqc-iot-sentinel) — IoT telemetry
- [`dabroiotexs-dao-decentralization`](https://github.com/AuditorSEC-Initiative/dabroiotexs-dao-decentralization) — DAO governance

---

## 🌍 Grant Eligibility

- **UHIP-2A**: Resource Integrity module for reconstruction risk
- **MaJoR EDF**: Dual-use resource monitoring (timber/amber in conflict zones)
- **EU Horizon Europe**: ESG compliance infrastructure
- **Gitcoin Grants**: Public goods — open ESG data for Ukraine
- **BRAVE1**: Defense-civilian resource integrity tool

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs for new resource types, detection rules, UI features always welcome.

## 🔒 Security

See [SECURITY.md](SECURITY.md).

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Built in Bakhmach, Chernihiv oblast 🇺🇦 — AuditorSEC Initiative*
