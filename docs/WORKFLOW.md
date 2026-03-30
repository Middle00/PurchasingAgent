# End-to-End Purchasing Workflow

## Principle: Human-in-the-Loop (HITL)

**The agent never places orders.** It detects, calculates, and stages. A human reviews and approves every purchase before it is submitted to a supplier.

---

## Phase 1: Reorder Detection & ClickUp Staging (Current)

```
BigQuery
  └── rtp_inventory_recomendations
        (items below days_supply threshold)
          │
          ▼
    Reorder Engine
    ┌─────────────────────────────────────────────────────┐
    │ 1. For each item below threshold:                   │
    │    a. Fetch product master (stg_uc_items)           │
    │    b. Get effective MOQ (corrections table first)   │
    │    c. UOM convert: sell-units needed → buy-units    │
    │    d. Round up to MOQ increment                     │
    │    e. Rank preferred suppliers by explicit code /   │
    │       category heuristic                            │
    │    f. Build ReorderRecommendation                   │
    └─────────────────────────────────────────────────────┘
          │
          ▼
    ClickUp Task (status: "to review")
    - Product name, SKU, manufacturer code
    - Current stock, burn rate, days supply
    - Recommended buy qty (buy-units + sell-unit equiv.)
    - Estimated cost
    - Preferred suppliers
    - Priority based on days supply (urgent/high/normal/low)
          │
          ▼
    Human Review → Approve or Adjust → Place Order Manually
```

### SKU Matching in Phase 1
- Supplier codes from product attributes are surfaced in the ClickUp task
- If no supplier code is stored, `normalize_code(manufacturer_code)` is shown
- Human buyer uses these to look up items on supplier sites

---

## Phase 2: Supplier Price & Stock Comparison (Planned)

```
ReorderRecommendation
    │
    ▼
SupplierCompareService.get_listings(product)
    │
    ├── For each supplier with a known code for this product:
    │     └── SupplierModule.get_listing(product)
    │           1. Use explicit supplier_code if available
    │           2. Else: normalize manufacturer_code → search supplier site
    │           3. Return: price, in_stock, stock_qty, url
    │
    ▼
Compare listings → rank by (in_stock, price_per_sell_unit)
    │
    ▼
Update ReorderRecommendation with live pricing and best supplier
    │
    ▼
ClickUp task now includes live price comparisons
```

### Normalization at Search Time
```python
# Preferred: use explicit supplier code
supplier_code = product.supplier_codes.for_supplier("beadsmith")  # "11-9401"

# Fallback: normalize manufacturer code
normalized = normalize_code(product.manufacturer_code)  # "401"
# Search Beadsmith for items matching normalized code
```

---

## Phase 3: Overnight Cart Building (Planned)

```
Scheduled Job (nightly, e.g., 2am ET)
    │
    ▼
Generate all ReorderRecommendations
    │
    ▼
For each recommendation:
    ├── Run supplier comparison (Phase 2)
    ├── Select best supplier per item
    └── Build CartItem record
    │
    ▼
Group CartItems by supplier → one cart per supplier
    │
    ▼
GoogleSheetsService.write_cart_summary(cart_items, spreadsheet_id)
    Sheet columns:
    | item_id | description | manufacturer_code | current_inventory |
    | cost | quantity_added | supplier | cart_name |
    │
    ▼
Buyer reviews Google Sheet in morning
    │
    ▼
Buyer places orders on supplier sites (or approves for Phase 4 automation)
```

---

## Phase 4: Feedback Loop (Planned)

```
After order is placed:
    ├── Record actual MOQ from invoice → update moq_corrections.json
    ├── Record actual lead time → update product master
    └── Record actual cost → update unit_cost
    │
    ▼
After goods are received:
    └── Compare to projected reorder quantities
        → Refine burn rate model if deviation > 10%
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ BigQuery (read-only)                                                 │
│   stg_uc_items ──────────────────────────────────────────────────┐  │
│   rtp_inventory_recomendations ──── Reorder Engine               │  │
│   algolia__potomacbeads_feed_items_unified (future enrichment)   │  │
└────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Reorder Engine    │
                    │  - MOQ corrections │ ←── data/moq_corrections.json
                    │  - UOM conversion  │
                    │  - SKU matching    │
                    └─────────┬──────────┘
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
         ClickUp API    Google Sheets    (Phase 2)
         (task staging) (cart summary)  Supplier Sites
```

---

## API Trigger Points

| Endpoint | Trigger | Description |
|----------|---------|-------------|
| `GET /reorder/recommendations` | On-demand | Preview recommendations without staging |
| `POST /reorder/stage` | On-demand or cron | Generate + push to ClickUp |
| `GET /inventory/below-threshold` | On-demand | Raw list of items below threshold |

**Recommended schedule:** Run `POST /reorder/stage` daily at 6am ET via Cloud Scheduler.
