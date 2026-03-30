# Supplier Profiles

## Overview

PotomacBeads sources from 5 primary suppliers. Many Czech bead SKUs are available from multiple suppliers — the purchasing agent compares price and availability before recommending a source.

**Primary items for online purchasing:**
- Miyuki / Toho seed beads (11/0, 8/0, 6/0, 15/0, Delicas)
- Czech shaped beads: SuperDuo, MiniDuo, drops, daggers, rounds, fire polished
- Tools (pliers, wire cutters, crimping tools)
- Gold-filled and sterling silver findings

---

## Supplier Directory

### Beadsmith (Helby Import)
- **URL:** https://www.beadsmith.com
- **Specialty:** Tools, findings, Miyuki/Toho seed beads, general supplies
- **Module:** `src/suppliers/beadsmith.py`
- **Requires account:** Yes
- **Code format:** `{size}-9{color_code}` — e.g., Miyuki 11/0 color 401 → `11-9401`
  - Strip size prefix and "9" separator to get core code: `401`
  - Also uses `{size}-{color_code}` for some product lines: `11-401` → `401`
- **Notes:** Default supplier for tools and findings. Competitive on Miyuki/Toho seed beads.

### Starman
- **URL:** https://www.starmanbeads.com
- **Specialty:** Czech beads — SuperDuo, MiniDuo, drops, daggers, fire polished, Rulla, Tinos
- **Module:** `src/suppliers/starman.py`
- **Requires account:** Yes
- **Code format:** `{size}/0-{color_code}` — e.g., `11/0-401` → core code `401`
- **Notes:** Primary source for Czech shaped beads. Compare price with All-Beads and G&B for overlapping SKUs.

### All-Beads
- **URL:** https://www.all-beads.com
- **Specialty:** Czech beads, broad selection
- **Module:** `src/suppliers/allbeads.py`
- **Requires account:** No
- **Notes:** Broad catalog, competitive pricing on Czech glass. Compare against Starman.

### Rutkovsky
- **URL:** https://www.rutkovsky.com
- **Specialty:** Czech glass beads
- **Module:** `src/suppliers/rutkovsky.py`
- **Requires account:** No
- **Notes:** Specialist in Czech glass. Strong on fire polished and round pressed glass.

### G&B Beads
- **URL:** https://www.gbbeads.com
- **Specialty:** Czech glass beads, shaped beads
- **Module:** `src/suppliers/gnb.py`
- **Requires account:** No
- **Notes:** Compare against Starman and All-Beads for SuperDuo, MiniDuo, and fire polished.

---

## SKU / Code Matching

### The Problem
The same product (e.g., Miyuki 11/0 color 401) is coded differently by each supplier:

| Source | Code |
|--------|------|
| Manufacturer | `401` |
| Beadsmith | `11-9401` |
| Starman | `11/0-401` |
| Internal SKU | `MIY-11-401` |

### Solution
The `src/utils/sku_matcher.py` module normalizes all codes to the core manufacturer code:
1. **Preferred:** Explicit supplier codes stored in product attributes (`supplier_codes.beadsmith`, etc.)
2. **Fallback:** Strip prefixes from manufacturer code using `normalize_code()` and fuzzy-match

### Supplier Code Storage
Supplier-specific codes are stored in the BigQuery product record as JSON attributes:
```json
{
  "supplier_codes": {
    "beadsmith": "11-9401",
    "starman": "11/0-401",
    "allbeads": null,
    "rutkovsky": null,
    "gnb": null
  }
}
```

When a code is present, the agent uses it directly. When absent, it falls back to `normalize_code(manufacturer_code)` and searches by that.

---

## Overlap Matrix

Items available from multiple suppliers (Phase 2 will compare live prices):

| Category | Beadsmith | Starman | All-Beads | Rutkovsky | G&B |
|----------|-----------|---------|-----------|-----------|-----|
| Miyuki Seed Beads | ✓ Primary | | | | |
| Toho Seed Beads | ✓ Primary | | | | |
| SuperDuo | | ✓ Primary | ✓ Compare | | ✓ Compare |
| MiniDuo | | ✓ Primary | ✓ Compare | | ✓ Compare |
| Fire Polished | | ✓ | ✓ Compare | ✓ Compare | ✓ Compare |
| Czech Rounds | | ✓ | ✓ | ✓ | ✓ |
| Daggers / Drops | | ✓ Primary | ✓ Compare | | |
| Tools | ✓ Primary | | | | |
| Findings | ✓ Primary | | | | |
