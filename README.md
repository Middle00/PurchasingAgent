# PurchasingAgent

Automated purchasing agent for Potomax Brands (PotomacBeads). Monitors inventory levels in BigQuery, identifies items needing reorder, compares prices and availability across multiple suppliers, builds shopping carts, and stages orders for human approval via ClickUp.

## Overview

This agent automates the purchasing workflow for PotomacBeads, a specialty bead retailer. It handles:

- **Inventory monitoring** — queries BigQuery for items below reorder thresholds
- **Reorder calculation** — applies UOM conversion and MOQ rounding to determine buy quantities
- **Supplier comparison** — compares price and availability across 5 suppliers (Phase 2)
- **Cart building** — constructs purchase carts overnight for morning review (Phase 3)
- **Order staging** — creates ClickUp tasks for human approval before any order is placed

## Key Principle: Human-in-the-Loop (HITL)

**No orders are ever placed automatically.** The agent builds carts and stages recommendations. A human reviews and approves before any purchase is submitted.

## Architecture

```
BigQuery (inventory data)
    ↓
Reorder Engine (threshold detection + UOM/MOQ calculation)
    ↓
Supplier Compare (price & availability — Phase 2)
    ↓
ClickUp (task staging for approval)
    ↓
Google Sheets (overnight cart summary — Phase 3)
```

## Phase Plan

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Reorder Detection & ClickUp Staging | In Progress |
| 2 | Supplier Price & Stock Comparison (browser automation) | Planned |
| 3 | Overnight Cart Building + Google Sheet summary | Planned |
| 4 | Feedback Loop (PO tracking, lead time learning, MOQ corrections) | Planned |

## Setup

### Prerequisites
- Python 3.12+
- GCP service account with BigQuery read access
- ClickUp API token
- Docker (for Cloud Run deployment)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID=potomax-brands
export BIGQUERY_SA_KEY='<base64-encoded service account JSON>'
export CLICKUP_API_TOKEN='<your token>'
export CLICKUP_LIST_ID='<your list id>'

# Run the API
uvicorn src.main:app --reload
```

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/reorder/recommendations` | Get current reorder recommendations |
| POST | `/reorder/stage` | Stage reorder recommendations to ClickUp |
| GET | `/inventory/below-threshold` | Items below reorder threshold |

## Project Structure

```
src/
├── main.py              # FastAPI entry point
├── config.py            # Settings and env vars
├── models/              # Pydantic data models
├── services/            # External integrations (BigQuery, ClickUp, Sheets)
├── suppliers/           # Supplier profiles and interfaces
└── utils/               # UOM conversion, MOQ handling, SKU matching
```

## Suppliers

- **Beadsmith (Helby Import)** — tools, findings, general supplies
- **Starman** — Czech beads (SuperDuo, MiniDuo, drops, daggers)
- **All-Beads** — Czech beads, broad selection
- **Rutkovsky** — Czech glass beads
- **G&B Beads** — Czech beads

See [docs/SUPPLIERS.md](docs/SUPPLIERS.md) for full profiles.
