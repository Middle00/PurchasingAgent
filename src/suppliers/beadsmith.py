"""
Beadsmith / Helby Import supplier module.

Primary supplier for tools, findings, Miyuki/Toho seed beads, and general supplies.
Website: https://www.beadsmith.com

Code format: "{size}-9{color_code}" or "{size}-{color_code}"
  e.g., Miyuki 11/0 color 401 → "11-9401"
  Normalize by stripping the size prefix and optional "9": core code = "401"

Phase 1: stub — returns empty listings.
Phase 2: Playwright browser automation.
"""

from src.models.supplier import Supplier, SupplierProductListing
from src.suppliers.base import BaseSupplier


class BeadsmithSupplier(BaseSupplier):
    @property
    def profile(self) -> Supplier:
        return Supplier(
            name="beadsmith",
            display_name="Beadsmith (Helby Import)",
            base_url="https://www.beadsmith.com",
            categories=[
                "Miyuki Seed Beads",
                "Toho Seed Beads",
                "Tools",
                "Findings",
                "Wire",
                "Stringing",
                "General Supplies",
            ],
            notes=(
                "Primary for tools, findings, and seed beads. "
                "Code format: size-9color e.g. '11-9401' for Miyuki 11/0 color 401."
            ),
            requires_account=True,
            supports_browser_automation=False,
        )
