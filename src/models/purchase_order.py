from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class POStatus(str, Enum):
    DRAFT = "draft"
    STAGED = "staged"        # Submitted to ClickUp for approval
    APPROVED = "approved"    # Human approved
    ORDERED = "ordered"      # Order placed with supplier
    RECEIVED = "received"    # Goods received
    CANCELLED = "cancelled"


class POLineItem(BaseModel):
    """A single line item in a purchase order."""

    sku: str
    product_name: str
    manufacturer_code: Optional[str] = None
    supplier_sku: Optional[str] = None
    quantity: int = Field(..., description="Quantity in buy-units")
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    notes: str = ""


class CartItem(BaseModel):
    """An item staged for the Google Sheets cart summary (Phase 3)."""

    item_id: str
    description: str
    manufacturer_code: Optional[str] = None
    current_inventory: int
    cost: Optional[Decimal] = None
    quantity_added: int
    supplier: str
    cart_name: str


class PurchaseOrder(BaseModel):
    """A purchase order staged for human approval."""

    po_id: str = Field(..., description="Internal PO ID")
    supplier_name: str
    status: POStatus = POStatus.DRAFT
    line_items: list[POLineItem] = Field(default_factory=list)
    total_estimated_cost: Optional[Decimal] = None

    clickup_task_id: Optional[str] = Field(None, description="ClickUp task ID once staged")
    clickup_task_url: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    ordered_at: Optional[datetime] = None
    notes: str = ""

    def add_line(self, item: POLineItem) -> None:
        self.line_items.append(item)
        self._recalculate_total()

    def _recalculate_total(self) -> None:
        costs = [li.total_cost for li in self.line_items if li.total_cost is not None]
        self.total_estimated_cost = sum(costs) if costs else None
