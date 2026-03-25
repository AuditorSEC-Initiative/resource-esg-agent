# Contributing to ResourceESGAgent

Thank you for your interest in contributing to **ResourceESGAgent**.

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/AuditorSEC-Initiative/resource-esg-agent
cd resource-esg-agent
```

### 2. Create a Branch

```bash
git checkout -b feature/my-resource-rule
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Make Changes

Contributions are welcome for:
- **New resource types** -- extend `RESOURCE_RULES` in `service.py`
- **Detection rules** -- improve hack pattern thresholds
- **API endpoints** -- new FastAPI routes in `api.py`
- **Tests** -- add rows to `tests/multi_resource.csv` or write pytest cases
- **Grafana panels** -- extend `grafana/dashboard.json`
- **k8s/Helm** -- improvements to `k8s/` charts

### 5. Run Tests

```bash
pytest tests/ -v
```

### 6. Submit a Pull Request

- Target branch: `main`
- Use Conventional Commits: `feat:`, `fix:`, `docs:`
- Reference issues with `Closes #123`

## Adding a New Resource Type

```python
# agents/resource_esg/service.py
RESOURCE_RULES["coal"] = {
    "hack_patterns": {"slag": [(100, 5000, "coking_coal")]},
    "critical_species": {"anthracite"}
}
```

No other changes required.

## Contact

Telegram: @AuditorSEC  
Email: info@auditorsec.com  
Built in Bakhmach, Chernihiv oblast UA
