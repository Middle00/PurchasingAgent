"""
All-Beads supplier module.

Czech beads with broad selection. Competitive on price for many Starman overlaps.
Website: https://www.all-beads.com

Phase 1: stub.
Phase 2: Playwright browser automation.
"""

from src.models.supplier import Supplier
from src.suppliers.base import BaseSupplier


class AllBeadsSupplier(BaseSupplier):
    @property
    def profile(self) -> Supplier:
        return Supplier(
            name="allbeads",
            display_name="All-Beads",
            base_url="https://www.all-beads.com",
            categories=[
                "SuperDuo",
                "MiniDuo",
                "Czech Pressed Glass",
                "Fire Polished",
                "Drops",
                "Daggers",
                "Seed Beads",
            ],
            notes="Broad Czech bead selection. Compare price against Starman for shaped beads.",
            requires_account=False,
            supports_browser_automation=False,
        )
