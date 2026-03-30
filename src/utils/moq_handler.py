"""
MOQ (Minimum Order Quantity) handler.

BigQuery MOQ data is often inaccurate. This module:
- Loads a persistent corrections table from data/moq_corrections.json
- Applies corrections before any MOQ rounding
- Provides a method to log new corrections (call when you spot a bad MOQ)
- Rounds order quantities UP to the nearest valid MOQ increment
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Corrections file schema:
# {
#   "SKU123": {
#     "moq": 12,
#     "increment": 12,
#     "note": "Listed as 72 in BQ but actually 12",
#     "updated_at": "2024-01-15T10:00:00"
#   }
# }


class MOQHandler:
    def __init__(self, corrections_path: str = "data/moq_corrections.json"):
        self.corrections_path = Path(corrections_path)
        self._corrections: dict[str, dict] = {}
        self._load_corrections()

    def _load_corrections(self) -> None:
        if self.corrections_path.exists():
            try:
                with open(self.corrections_path) as f:
                    self._corrections = json.load(f)
                logger.debug(f"Loaded {len(self._corrections)} MOQ corrections from {self.corrections_path}")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not load MOQ corrections file: {e}")
                self._corrections = {}
        else:
            logger.debug(f"No MOQ corrections file found at {self.corrections_path}")
            self._corrections = {}

    def get_effective_moq(self, sku: str, bq_moq: int) -> int:
        """Return the corrected MOQ for a SKU, or the BigQuery value if no correction exists."""
        if sku in self._corrections and "moq" in self._corrections[sku]:
            corrected = self._corrections[sku]["moq"]
            if corrected != bq_moq:
                logger.debug(f"SKU {sku}: using corrected MOQ {corrected} (BQ had {bq_moq})")
            return corrected
        return bq_moq

    def get_effective_increment(self, sku: str, bq_increment: int) -> int:
        """Return the corrected order increment for a SKU."""
        if sku in self._corrections and "increment" in self._corrections[sku]:
            return self._corrections[sku]["increment"]
        return bq_increment

    def round_up_to_moq(self, quantity: int, moq: int, increment: int | None = None) -> int:
        """
        Round a raw quantity up to the nearest valid MOQ increment.

        Rules:
        - If quantity <= 0, return moq (minimum possible order)
        - If quantity < moq, return moq
        - If quantity > moq, round up to moq + N * increment

        Examples:
            round_up_to_moq(1, moq=12, increment=12)  → 12
            round_up_to_moq(12, moq=12, increment=12) → 12
            round_up_to_moq(20, moq=12, increment=12) → 24
            round_up_to_moq(25, moq=12, increment=12) → 36
            round_up_to_moq(5, moq=6, increment=6)    → 6
        """
        if moq <= 0:
            moq = 1
        inc = increment if (increment and increment > 0) else moq

        if quantity <= 0:
            return moq
        if quantity <= moq:
            return moq

        # How many increments above moq do we need?
        above_moq = quantity - moq
        multiples_needed = math.ceil(above_moq / inc)
        return moq + (multiples_needed * inc)

    def log_correction(
        self,
        sku: str,
        corrected_moq: int,
        corrected_increment: int | None = None,
        note: str = "",
    ) -> None:
        """
        Record a MOQ correction for a SKU.

        This persists to the corrections JSON file and takes effect on the next run.
        Call this whenever a supplier order reveals an incorrect MOQ in BigQuery.
        """
        self._corrections[sku] = {
            "moq": corrected_moq,
            "increment": corrected_increment if corrected_increment is not None else corrected_moq,
            "note": note,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._save_corrections()
        logger.info(f"Logged MOQ correction for SKU {sku}: moq={corrected_moq}, increment={corrected_increment}")

    def remove_correction(self, sku: str) -> bool:
        """Remove a correction for a SKU (revert to BigQuery value)."""
        if sku in self._corrections:
            del self._corrections[sku]
            self._save_corrections()
            logger.info(f"Removed MOQ correction for SKU {sku}")
            return True
        return False

    def list_corrections(self) -> dict[str, dict]:
        """Return all current MOQ corrections."""
        return dict(self._corrections)

    def _save_corrections(self) -> None:
        self.corrections_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.corrections_path, "w") as f:
            json.dump(self._corrections, f, indent=2)
