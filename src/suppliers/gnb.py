"""
G&B Beads supplier module.

Czech glass bead supplier.
Website: https://www.gbbeads.com

Phase 1: stub.
Phase 2: Playwright browser automation.
"""

from src.models.supplier import Supplier
from src.suppliers.base import BaseSupplier


class GNBSupplier(BaseSupplier):
    @property
    def profile(self) -> Supplier:
        return Supplier(
            name="gnb",
            display_name="G&B Beads",
            base_url="https://www.gbbeads.com",
            categories=[
                "Czech Glass Beads",
                "SuperDuo",
                "MiniDuo",
                "Fire Polished",
                "Czech Pressed Glass",
            ],
            notes="Czech beads. Compare price for shaped and pressed glass SKUs.",
            requires_account=False,
            supports_browser_automation=False,
        )
