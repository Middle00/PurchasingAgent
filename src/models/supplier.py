from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SupplierProductListing(BaseModel):
    """A product as listed by a specific supplier."""

    supplier_name: str
    supplier_sku: str = Field(..., description="Supplier's own item code")
    normalized_code: Optional[str] = Field(
        None, description="Core manufacturer code after normalization (e.g., '401')"
    )
    price: Decimal = Field(..., description="Price per buy-unit")
    in_stock: bool = Field(default=True)
    stock_qty: Optional[int] = Field(None, description="Available quantity if known")
    url: Optional[str] = Field(None, description="Product page URL")
    notes: Optional[str] = None


class Supplier(BaseModel):
    """Supplier profile."""

    name: str
    display_name: str
    base_url: str
    categories: list[str] = Field(default_factory=list, description="Product categories this supplier carries")
    notes: str = ""
    requires_account: bool = False
    supports_browser_automation: bool = False  # True once Phase 2 is implemented
