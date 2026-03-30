"""
Supplier price and availability comparison.

Phase 1: Stub — returns empty results.
Phase 2: Will use browser automation to query each supplier's website.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.models.supplier import SupplierProductListing

if TYPE_CHECKING:
    from src.models.product import Product

logger = logging.getLogger(__name__)


class SupplierCompareService:
    """
    Compares price and availability for a product across all configured suppliers.

    Phase 2 implementation will:
    - Use Playwright browser automation per supplier module
    - Normalize SKU codes using sku_matcher before querying
    - Prefer explicit supplier codes from product attributes
    - Fall back to fuzzy manufacturer code matching
    - Cache results to avoid redundant browser sessions
    """

    def get_listings(self, product: "Product") -> list[SupplierProductListing]:
        """
        Fetch live price/availability listings for a product from all suppliers.

        Phase 1: returns empty list (no browser automation yet).
        Phase 2: will query each supplier module in parallel.
        """
        logger.debug(f"Phase 2 not yet implemented — no live listings for SKU {product.sku}")
        return []

    def best_price(self, listings: list[SupplierProductListing]) -> SupplierProductListing | None:
        """Return the cheapest in-stock listing."""
        in_stock = [l for l in listings if l.in_stock]
        if not in_stock:
            return None
        return min(in_stock, key=lambda l: l.price)
