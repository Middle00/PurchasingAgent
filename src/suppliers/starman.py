"""
Starman supplier module.

Czech beads specialist — SuperDuo, MiniDuo, drops, daggers, fire polished.
Website: https://www.starmanbeads.com

Phase 1: stub.
Phase 2: Playwright browser automation.
"""

from src.models.supplier import Supplier
from src.suppliers.base import BaseSupplier


class StarmanSupplier(BaseSupplier):
    @property
    def profile(self) -> Supplier:
        return Supplier(
            name="starman",
            display_name="Starman",
            base_url="https://www.starmanbeads.com",
            categories=[
                "SuperDuo",
                "MiniDuo",
                "Daggers",
                "Drops",
                "Fire Polished",
                "Czech Pressed Glass",
                "Rulla",
                "Tinos",
                "Preciosa",
            ],
            notes=(
                "Primary Czech bead supplier. Broad selection of shaped beads. "
                "Price comparison with All-Beads and G&B for overlapping SKUs."
            ),
            requires_account=True,
            supports_browser_automation=False,
        )
