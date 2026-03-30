"""
Rutkovsky supplier module.

Czech glass bead specialist.
Website: https://www.rutkovsky.com

Phase 1: stub.
Phase 2: Playwright browser automation.
"""

from src.models.supplier import Supplier
from src.suppliers.base import BaseSupplier


class RutkovskySupplier(BaseSupplier):
    @property
    def profile(self) -> Supplier:
        return Supplier(
            name="rutkovsky",
            display_name="Rutkovsky",
            base_url="https://www.rutkovsky.com",
            categories=[
                "Czech Glass Beads",
                "Fire Polished",
                "Czech Pressed Glass",
                "Round Beads",
            ],
            notes="Czech glass beads. Compare price for fire polished and round pressed glass.",
            requires_account=False,
            supports_browser_automation=False,
        )
