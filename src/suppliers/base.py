"""
Base supplier interface.

All supplier modules implement this interface. Phase 1 stubs return empty results.
Phase 2 implementations will add Playwright browser automation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.models.supplier import Supplier, SupplierProductListing
from src.utils.sku_matcher import SKUMatcher, normalize_code

if TYPE_CHECKING:
    from src.models.product import Product


class BaseSupplier(ABC):
    """Abstract base class for all supplier integrations."""

    sku_matcher = SKUMatcher()

    @property
    @abstractmethod
    def profile(self) -> Supplier:
        """Return the supplier's static profile."""
        ...

    def get_listing(self, product: "Product") -> SupplierProductListing | None:
        """
        Look up a product on this supplier's website and return a listing.

        Strategy:
        1. If the product has an explicit supplier code for this supplier, use it.
        2. Otherwise, normalize the manufacturer code and search by that.
        3. Return None if not found or not available.

        Phase 1: returns None (stub).
        Phase 2: uses Playwright automation.
        """
        supplier_code = product.supplier_codes.for_supplier(self.profile.name)
        if supplier_code:
            return self._fetch_by_supplier_code(supplier_code, product)
        elif product.manufacturer_code:
            normalized = normalize_code(product.manufacturer_code)
            return self._fetch_by_manufacturer_code(normalized, product)
        return None

    def _fetch_by_supplier_code(
        self, supplier_code: str, product: "Product"
    ) -> SupplierProductListing | None:
        """
        Fetch a listing using the supplier's own item code.
        Phase 2: implement with browser automation.
        """
        return None

    def _fetch_by_manufacturer_code(
        self, normalized_code: str, product: "Product"
    ) -> SupplierProductListing | None:
        """
        Search for a product using the normalized manufacturer code.
        Phase 2: implement with browser automation + fuzzy matching.
        """
        return None
