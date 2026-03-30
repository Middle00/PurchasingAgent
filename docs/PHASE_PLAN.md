# Phase Plan

## Phase 1: Reorder Detection & Staging
**Status:** In Progress

### Goals
- Query BigQuery for items below days-supply threshold
- Calculate correct buy quantities with UOM conversion and MOQ rounding
- Stage reorder recommendations as ClickUp tasks for human approval

### Deliverables
- [x] FastAPI service with health and reorder endpoints
- [x] BigQuery integration (read inventory + product master)
- [x] UOM converter (seed bead pack → tube conversion)
- [x] MOQ handler with persistent corrections table
- [x] SKU matcher / code normalizer
- [x] Reorder engine
- [x] ClickUp task staging
- [x] Docker + Cloud Run deployment
- [ ] Cloud Scheduler trigger (daily 6am ET)
- [ ] ClickUp list ID configured in Cloud Run env vars

### Success Criteria
- All items below 30-day supply threshold appear in ClickUp within 1 hour of daily run
- Recommended quantities account for UOM conversion and MOQ constraints
- MOQ corrections table overrides bad BigQuery values correctly

---

## Phase 2: Supplier Price & Stock Comparison
**Status:** Planned

### Goals
- For each reorder item, query 1–5 suppliers for current price and availability
- Rank suppliers by (in-stock, price per sell-unit)
- Include live pricing in ClickUp tasks

### Approach
- Playwright browser automation per supplier module
- SKU matching: prefer explicit supplier codes, fall back to normalized manufacturer code
- Results cached per session to avoid redundant browser launches

### Deliverables
- [ ] Playwright integration in `BaseSupplier`
- [ ] `BeadsmithSupplier._fetch_by_supplier_code()` implementation
- [ ] `StarmanSupplier._fetch_by_supplier_code()` implementation
- [ ] `AllBeadsSupplier._fetch_by_manufacturer_code()` implementation
- [ ] `RutkovskySupplier._fetch_by_manufacturer_code()` implementation
- [ ] `GNBSupplier._fetch_by_manufacturer_code()` implementation
- [ ] `SupplierCompareService.get_listings()` live implementation
- [ ] Price-per-sell-unit normalization across UOM differences

### Success Criteria
- For any reorder item available at 2+ suppliers, the ClickUp task shows the price comparison
- Agent selects lowest in-stock price for the recommendation

---

## Phase 3: Overnight Cart Building
**Status:** Planned

### Goals
- Automated nightly run builds complete supplier carts
- Buyer wakes up to a Google Sheet summarizing what to order and from where
- Carts are organized by supplier, ready for same-day ordering

### Deliverables
- [ ] Nightly scheduled Cloud Run job
- [ ] Cart builder: groups items by preferred supplier
- [ ] `GoogleSheetsService.write_cart_summary()` implementation (gspread)
- [ ] Configurable target Google Sheet ID
- [ ] Notification to buyer (email or Slack) when sheet is ready

### Sheet Format
| item_id | description | manufacturer_code | current_inventory | cost | quantity_added | supplier | cart_name |
|---------|-------------|-------------------|------------------|------|---------------|---------|-----------|

### Success Criteria
- Sheet is ready by 7am ET each business day
- All items with < 30 days supply are represented
- Cart totals by supplier are summarized on a summary tab

---

## Phase 4: Feedback Loop
**Status:** Planned

### Goals
- Learn from completed orders to improve future recommendations
- Automatically correct MOQ data when invoices reveal discrepancies
- Refine burn rate model from actual vs. projected sell-through

### Deliverables
- [ ] PO tracking: record when orders are placed and received
- [ ] Automatic MOQ correction when invoice quantity differs from recommendation
- [ ] Lead time tracking per supplier per category
- [ ] Burn rate model refinement (compare projected vs. actual sell-through at reorder)
- [ ] Dashboard: in-stock rate, reorder accuracy, cost per unit trends

### Success Criteria
- After 3 months: MOQ correction table covers 80%+ of active SKUs
- Reorder recommendations hit target days-supply within ±10% of goal
- In-stock rate ≥ 95% across active SKUs
