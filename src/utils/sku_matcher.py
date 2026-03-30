"""
SKU / manufacturer code normalizer.

Suppliers all have their own code formatting for the same manufacturer item:
  Manufacturer: "401"
  Beadsmith:    "11-9401"  (size prefix + "9" + code)
  Starman:      "11/0-401" (size/0-code)
  Miyuki raw:   "401"
  Toho raw:     "401"

The core matching key is the manufacturer's color/item code (e.g., "401").
This module normalizes codes from any source to extract that core key,
enabling cross-supplier matching even when no explicit supplier code is stored.
"""

from __future__ import annotations

import re


# Patterns that represent supplier-specific prefixes or wrappers around the core code.
# Applied in order; the first match wins.
_NORMALIZATION_RULES: list[tuple[str, re.Pattern, str]] = [
    # Beadsmith: "11-9401" → "401"  (strip size-dash-9 prefix)
    # Also handles "11-401" → "401"
    ("beadsmith_size_prefix", re.compile(r"^\d+[/-]\d*(\d{3,})$"), r"\1"),
    # Starman: "11/0-401" → "401"
    ("starman_size_prefix", re.compile(r"^\d+/\d+-(\d+)$"), r"\1"),
    # Generic "AB-123" style prefix: strip leading letters/numbers and dash/slash
    ("generic_prefix", re.compile(r"^[A-Za-z0-9]{1,4}[-/]([A-Za-z0-9]+)$"), r"\1"),
    # Leading zeros: "0401" → "401"
    ("leading_zeros", re.compile(r"^0+(\d+)$"), r"\1"),
]


def normalize_code(raw_code: str) -> str:
    """
    Strip supplier-specific prefixes and return the core manufacturer code.

    Examples:
        normalize_code("11-9401")  → "401"
        normalize_code("11-401")   → "401"
        normalize_code("11/0-401") → "401"
        normalize_code("401")      → "401"
        normalize_code("0401")     → "401"
        normalize_code("SDB-401")  → "401"
    """
    code = raw_code.strip()

    for _name, pattern, replacement in _NORMALIZATION_RULES:
        match = pattern.fullmatch(code)
        if match:
            # Apply the replacement to extract the core code
            result = pattern.sub(replacement, code)
            # Recurse once in case the result still has a prefix
            if result != code:
                return normalize_code(result)

    return code


def codes_match(code_a: str, code_b: str) -> bool:
    """Return True if two codes refer to the same manufacturer item after normalization."""
    return normalize_code(code_a) == normalize_code(code_b)


class SKUMatcher:
    """
    Matches a product to supplier listings using normalized manufacturer codes.

    Usage:
        matcher = SKUMatcher()
        # Prefer explicit supplier code from product attributes
        supplier_code = product.supplier_codes.for_supplier("beadsmith")
        if supplier_code:
            listing = find_by_exact_code(supplier_code)
        else:
            # Fall back to fuzzy manufacturer code matching
            listing = matcher.find_best_match(product.manufacturer_code, supplier_listings)
    """

    def find_best_match(
        self,
        manufacturer_code: str | None,
        supplier_listings: list[dict],
        code_field: str = "supplier_sku",
    ) -> dict | None:
        """
        Find the best matching supplier listing for a given manufacturer code.

        Args:
            manufacturer_code: The core manufacturer color/item code (e.g., "401").
            supplier_listings: List of dicts with at least a `code_field` key.
            code_field: Key in each listing dict that holds the supplier's item code.

        Returns:
            Best matching listing dict, or None if no match.
        """
        if not manufacturer_code:
            return None

        normalized_target = normalize_code(manufacturer_code)

        for listing in supplier_listings:
            raw = listing.get(code_field, "")
            if raw and normalize_code(str(raw)) == normalized_target:
                return listing

        return None

    def normalize_all(self, codes: list[str]) -> list[str]:
        """Normalize a list of codes."""
        return [normalize_code(c) for c in codes]
