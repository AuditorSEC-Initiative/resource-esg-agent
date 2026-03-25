# ResourceESGAgent React UI

React dashboard for the ResourceESGAgent ESG risk detection system.

## Features

- **ESG Risk Map** — geographic heatmap of enterprise risk scores
- **Pie/Bar Charts** — risk distribution by resource type (timber/amber/ore)
- **Shipment Table** — filterable, sortable, searchable
- **PDF Export** — one-click report generation
- **Real-time** — auto-refresh every 30s from FastAPI backend

## Tech Stack

- React 18 + Vite
- Recharts (charts)
- React-Leaflet (maps)
- Axios (API client)
- jsPDF (PDF export)
- Tailwind CSS

## Quick Start

```bash
npm install
npm run dev
```

Open http://localhost:5173

## Build

```bash
npm run build
# Output: dist/
```

## Environment

Create `.env.local`:
```
VITE_API_URL=http://localhost:8000
```

## API Integration

Connects to FastAPI endpoints:
- `GET /api/v1/esg/resource/{enterprise_id}/{period}`
- `GET /api/v1/esg/resource/{enterprise_id}/shipments`
- `POST /api/v1/esg/resource/shipments`
