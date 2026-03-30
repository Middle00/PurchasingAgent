"""ClickUp integration — create reorder approval tasks."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from src.models.reorder import ReorderRecommendation

if TYPE_CHECKING:
    from src.config import Settings

logger = logging.getLogger(__name__)

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


class ClickUpService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.headers = {
            "Authorization": settings.clickup_api_token,
            "Content-Type": "application/json",
        }

    def create_reorder_task(self, rec: ReorderRecommendation) -> str:
        """Create a ClickUp task for a reorder recommendation. Returns the task ID."""
        cost_str = (
            f"${rec.estimated_total_cost:,.2f}"
            if rec.estimated_total_cost is not None
            else "Cost TBD"
        )
        suppliers_str = ", ".join(rec.preferred_suppliers) if rec.preferred_suppliers else "TBD"

        description = (
            f"**Reorder Recommendation — {rec.product_name}**\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| SKU | {rec.sku} |\n"
            f"| Manufacturer Code | {rec.manufacturer_code or 'N/A'} |\n"
            f"| Category | {rec.category} |\n"
            f"| Current Stock | {rec.current_stock_sell_units} units |\n"
            f"| Daily Burn Rate | {rec.daily_burn_rate:.1f} units/day |\n"
            f"| Days Supply | {rec.days_supply:.0f} days |\n"
            f"| Recommended Qty | {rec.recommended_buy_qty} buy-units |\n"
            f"| Sell-Unit Equivalent | {rec.recommended_buy_qty_sell_units} units |\n"
            f"| Days Supply After Order | {rec.days_supply_after_order:.0f} days |\n"
            f"| Lead Time | {rec.lead_time_days} days |\n"
            f"| Estimated Cost | {cost_str} |\n"
            f"| Preferred Suppliers | {suppliers_str} |\n\n"
            f"**Notes:** {rec.notes}\n\n"
            f"⚠️ This is a recommendation only. Review and approve before placing order."
        )

        payload = {
            "name": f"Reorder: {rec.product_name} (SKU {rec.sku})",
            "description": description,
            "status": "to review",
            "priority": self._days_to_priority(rec.days_supply),
            "tags": ["purchasing", "reorder", rec.category.lower().replace(" ", "-")],
            "custom_fields": [
                {"name": "SKU", "value": rec.sku},
                {"name": "Days Supply", "value": str(int(rec.days_supply))},
                {"name": "Recommended Qty", "value": str(rec.recommended_buy_qty)},
            ],
        }

        url = f"{CLICKUP_API_BASE}/list/{self.settings.clickup_list_id}/task"
        response = httpx.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()

        task_id = response.json()["id"]
        logger.info(f"Created ClickUp task {task_id} for SKU {rec.sku}")
        return task_id

    def _days_to_priority(self, days_supply: float) -> int:
        """Map days of supply to ClickUp priority (1=urgent, 2=high, 3=normal, 4=low)."""
        if days_supply <= 7:
            return 1  # urgent
        elif days_supply <= 14:
            return 2  # high
        elif days_supply <= 21:
            return 3  # normal
        return 4  # low
