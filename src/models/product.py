from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SupplierCodes(BaseModel):
    """Supplier-specific item codes for a product.

    Each supplier reformats the manufacturer color/item code differently.
    Prefer these explicit codes over fuzzy matching when available.
    Example: manufacturer code '401' → beadsmith '11-9401', starman '11/0-401'
    """

    beadsmith: Optional[str] = None
    starman: Optional[str] = None
    allbeads: Optional[str] = None
    rutkovsky: Optional[str] = None
    gnb: Optional[str] = None

    def for_supplier(self, supplier_name: str) -> Optional[str]:
        """Return the supplier-specific code by supplier name, or None."""
        return getattr(self, supplier_name.lower().replace("-", "").replace("&", ""), None)


class Product(BaseModel):
    """Product master record from BigQuery stg_uc_items."""

    sku: str = Field(..., description="Internal SKU / item ID")
    name: str = Field(..., description="Product display name")
    category: str = Field(default="", description="Product category (e.g., Seed Beads, Czech Beads, Tools)")
    manufacturer: Optional[str] = Field(None, description="Brand / manufacturer (e.g., Miyuki, Toho, Starman)")
    manufacturer_code: Optional[str] = Field(
        None,
        description="Core manufacturer color/item code (e.g., '401'). Normalized — no prefix or suffix.",
    )
    supplier_codes: SupplierCodes = Field(
        default_factory=SupplierCodes,
        description="Supplier-specific item codes pulled from product attributes",
    )

    # Units of measure
    sell_uom: str = Field(default="EA", description="Unit sold to end customer (e.g., TU for tube, EA for each)")
    buy_uom: str = Field(default="EA", description="Unit purchased from supplier (e.g., PK for pack, BG for bag)")
    uom_conversion_factor: Optional[Decimal] = Field(
        None,
        description="How many sell-units per buy-unit. Populated by UOM converter.",
    )

    # Ordering constraints
    moq: int = Field(default=1, description="Minimum order quantity (in buy-units)")
    moq_increment: int = Field(default=1, description="Order increment after MOQ (defaults to MOQ)")
    lead_time_days: int = Field(default=14, description="Typical lead time from preferred supplier")

    # Cost
    unit_cost: Optional[Decimal] = Field(None, description="Cost per buy-unit from preferred supplier")

    # Inventory
    current_stock: int = Field(default=0, description="Actual on-hand quantity in sell-units")
    reorder_point: int = Field(default=0, description="Reorder trigger level in sell-units")
    days_supply: Optional[float] = Field(None, description="Current days of supply at current burn rate")
    daily_burn_rate: Optional[float] = Field(None, description="Average daily sell-through in sell-units")
