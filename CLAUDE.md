# PurchasingAgent — Claude Code Context

## Project
Automated purchasing agent for **Potomax Brands (PotomacBeads)**. Monitors BigQuery inventory, identifies reorder candidates, compares supplier pricing, builds carts, and stages orders for human approval.

## GCP Configuration
- **Project:** `potomax-brands`
- **BigQuery dataset (production):** `scalelean_production`
- **BigQuery dataset (dbt):** `dbt_clickthrunetwork`

### Key BigQuery Tables
| Table | Purpose |
|-------|---------|
| `scalelean_production.stg_uc_items` | Product master: SKU, name, category, UOM, MOQ, cost, lead time, supplier codes |
| `dbt_clickthrunetwork.rtp_inventory_recomendations` | Items below days-supply threshold with burn rates |
| `scalelean_production.algolia__potomacbeads_feed_items_unified` | Unified product feed including attributes and supplier-specific codes |

### GitHub Secrets Available
- `BIGQUERY_SA_KEY` — Base64-encoded BigQuery service account JSON
- `GCP_PROJECT_ID` — GCP project ID (`potomax-brands`)
- `GCP_SA_KEY` — Cloud Run deployment service account

## Critical Business Rules

### HITL Mandatory
**Never auto-place orders.** The agent's job is to:
1. Detect what needs ordering
2. Determine quantities
3. Build carts / stage recommendations
4. Wait for human approval

### Phantom Buffer Rule
Always report **3 fewer units** than actual inventory to marketplaces. This buffer prevents overselling during replenishment windows. Do NOT subtract the phantom buffer when calculating reorder quantities — use actual inventory.

### Target In-Stock Rate
**95%+** across all active SKUs.

### UOM Conversion
- Seed beads (Miyuki, Toho) are **bought in bulk** (100g or 250g packs) and **sold in tubes** (8.5g or 14g)
- Conversion tables are defined in `src/utils/uom_converter.py`
- Always convert buy-pack quantities to sell-unit equivalents when evaluating stock coverage
- Category-specific conversion tables take precedence over defaults

### MOQ Handling
- MOQ data in BigQuery is often inaccurate (e.g., listed as 72, actually 12)
- Use the corrections table (`data/moq_corrections.json`) for known overrides
- When a bad MOQ is identified, log it to the corrections table — it will take precedence on future runs
- Round UP to the nearest valid MOQ increment (e.g., need 20 with MOQ=12 → order 24)

## SKU / Code Matching
- Common matching key is the **manufacturer's color/item code** (e.g., `401`)
- Suppliers reformat codes differently: Beadsmith `11-9401`, Starman `11/401`, Miyuki `401`
- The `sku_matcher.py` utility normalizes codes by stripping prefixes and extracting the core code
- Product attributes in BigQuery may contain supplier-specific codes — prefer these over fuzzy matching when available

## Supplier Priority
When multiple suppliers stock the same item:
1. Check price per unit (after UOM conversion)
2. Check current availability
3. Apply any preference rules (e.g., Starman for Czech beads, Beadsmith for tools)

## Services Architecture
- **BigQuery service** (`services/bigquery.py`) — read-only, inventory and product data
- **ClickUp service** (`services/clickup.py`) — creates reorder approval tasks
- **Sheets service** (`services/sheets.py`) — generates overnight cart summary Google Sheet
- **Supplier modules** (`suppliers/`) — Phase 2 browser automation, Phase 1 stubs only

## Deployment
- Deployed to **Google Cloud Run** via GitHub Actions
- Workflow: `.github/workflows/main.yml`
- Docker image built and pushed to GCR on merge to `main`

## Development Notes
- Python 3.12+, FastAPI, Pydantic v2
- Tests in `tests/` — run with `pytest`
- Mock BigQuery data available for local testing in `tests/fixtures/`
- Do not hardcode credentials — all secrets via environment variables
