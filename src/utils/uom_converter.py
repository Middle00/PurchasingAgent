"""
Unit-of-measure conversion for purchasing calculations.

Beads are purchased in bulk (100g or 250g packs) but sold in tubes (8.5g or 14g).
This converter calculates how many buy-packs are needed to produce X sell-units.
"""

from __future__ import annotations

from decimal import Decimal

# Conversion table: (category_key, buy_uom, sell_uom) → sell_units_per_buy_unit
# A conversion factor of 11.76 means 1 100g pack yields ~11.76 8.5g tubes.
#
# Miyuki / Toho seed beads:
#   100g pack → 8.5g tubes: 100 / 8.5 ≈ 11.76
#   100g pack → 14g tubes:  100 / 14  ≈  7.14
#   250g pack → 8.5g tubes: 250 / 8.5 ≈ 29.41
#   250g pack → 14g tubes:  250 / 14  ≈ 17.86

_CONVERSION_TABLE: dict[tuple[str, str, str], float] = {
    # (category_keyword, buy_uom, sell_uom): sell_units_per_buy_unit
    ("seed_bead_100g", "PK", "TU"): 11.76,   # 100g pack → 8.5g tube
    ("seed_bead_100g", "PK", "TU14"): 7.14,  # 100g pack → 14g tube
    ("seed_bead_250g", "PK", "TU"): 29.41,   # 250g pack → 8.5g tube
    ("seed_bead_250g", "PK", "TU14"): 17.86, # 250g pack → 14g tube
    # Czech beads are typically sold and bought by the same unit (strand, gram, piece)
    ("czech_bead", "PK", "EA"): 1.0,
    ("czech_bead", "EA", "EA"): 1.0,
}

# Category name fragments that map to conversion category keys
_CATEGORY_MAP: dict[str, str] = {
    "miyuki": "seed_bead_100g",
    "toho": "seed_bead_100g",
    "seed bead": "seed_bead_100g",
    "11/0": "seed_bead_100g",
    "8/0": "seed_bead_100g",
    "6/0": "seed_bead_250g",
    "15/0": "seed_bead_100g",
    "superduo": "czech_bead",
    "miniduo": "czech_bead",
    "czech": "czech_bead",
    "fire polished": "czech_bead",
    "drop": "czech_bead",
    "dagger": "czech_bead",
}


class UOMConverter:
    def __init__(self, extra_conversions: dict[tuple[str, str, str], float] | None = None):
        self._table = dict(_CONVERSION_TABLE)
        if extra_conversions:
            self._table.update(extra_conversions)

    def get_conversion_factor(
        self,
        category: str,
        sell_uom: str,
        buy_uom: str,
        explicit_factor: Decimal | float | None = None,
    ) -> float:
        """
        Return how many sell-units are produced by one buy-unit.

        Priority:
        1. explicit_factor from the product record (set in BigQuery)
        2. Lookup by category + UOM combination
        3. Default to 1.0 (no conversion — buy and sell in same unit)
        """
        if explicit_factor is not None:
            return float(explicit_factor)

        # Normalize inputs
        cat_lower = category.lower()
        sell = sell_uom.upper()
        buy = buy_uom.upper()

        # Same unit — no conversion needed
        if buy == sell:
            return 1.0

        # Find a matching category key
        cat_key = self._classify_category(cat_lower)
        if cat_key:
            lookup = (cat_key, buy, sell)
            if lookup in self._table:
                return self._table[lookup]

        # No match found — default to 1.0 with a log-worthy note
        return 1.0

    def buy_units_needed(
        self,
        sell_units_needed: int,
        category: str,
        sell_uom: str,
        buy_uom: str,
        explicit_factor: Decimal | float | None = None,
    ) -> int:
        """
        Calculate how many buy-units are needed to produce sell_units_needed sell-units.
        Always rounds UP (ceil) because partial packs cannot be ordered.
        """
        import math
        factor = self.get_conversion_factor(category, sell_uom, buy_uom, explicit_factor)
        if factor <= 0:
            raise ValueError(f"Invalid conversion factor: {factor}")
        return math.ceil(sell_units_needed / factor)

    def sell_units_from_buy(
        self,
        buy_units: int,
        category: str,
        sell_uom: str,
        buy_uom: str,
        explicit_factor: Decimal | float | None = None,
    ) -> int:
        """Calculate how many sell-units result from a given number of buy-units."""
        import math
        factor = self.get_conversion_factor(category, sell_uom, buy_uom, explicit_factor)
        return math.floor(buy_units * factor)

    def _classify_category(self, category_lower: str) -> str | None:
        """Map a product category string to a conversion category key."""
        for fragment, key in _CATEGORY_MAP.items():
            if fragment in category_lower:
                return key
        return None
