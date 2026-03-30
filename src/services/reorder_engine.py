"""Reorder engine — core logic for detecting items that need ordering and calculating buy quantities."""

from __future__ import annotations

import logging
import math
from decimal import Decimal
from typing import TYPE_CHECKING

from src.models.product import Product
from src.models.reorder import ReorderRecommendation
from src.utils.moq_handler import MOQHandler
from src.utils.uom_converter import UOMConverter

if TYPE_CHECKING:
    from src.config import Settings
    from src.services.bigquery import BigQueryService

logger = logging.getLogger(__name__)

# Target days of supply after an order is placed
TARGET_DAYS_SUPPLY = 60


class ReorderEngine:
    def __init__(self, settings: Settings, bq_service: BigQueryService):
        self.settings = settings
        self.bq = bq_service
        self.uom = UOMConverter()
        self.moq_handler = MOQHandler(settings.moq_corrections_path)

    def generate_recommendations(self) -> list[ReorderRecommendation]:
        """
        Main entry point. Queries BigQuery for items below threshold,
        then calculates buy quantities with UOM conversion and MOQ rounding.
        """
        products = self.bq.get_items_below_threshold()
        logger.info(f"Found {len(products)} items below threshold")

        recommendations = []
        for product in products:
            try:
                rec = self._build_recommendation(product)
                if rec is not None:
                    recommendations.append(rec)
            except Exception as e:
                logger.error(f"Error building recommendation for SKU {product.sku}: {e}")

        # Sort by days_supply ascending (most urgent first)
        recommendations.sort(key=lambda r: r.days_supply)
        return recommendations

    def _build_recommendation(self, product: Product) -> ReorderRecommendation | None:
        """Build a single reorder recommendation for a product."""
        burn_rate = product.daily_burn_rate
        if burn_rate is None or burn_rate <= 0:
            logger.debug(f"SKU {product.sku}: no burn rate, skipping")
            return None

        days_supply = product.days_supply or 0
        current_stock = product.current_stock

        # How many sell-units do we need to reach TARGET_DAYS_SUPPLY?
        sell_units_needed = math.ceil(burn_rate * TARGET_DAYS_SUPPLY) - current_stock
        if sell_units_needed <= 0:
            return None

        # Convert sell-units needed → buy-units
        conversion_factor = self.uom.get_conversion_factor(
            category=product.category,
            sell_uom=product.sell_uom,
            buy_uom=product.buy_uom,
            explicit_factor=product.uom_conversion_factor,
        )
        buy_units_raw = math.ceil(sell_units_needed / conversion_factor)

        # Apply MOQ rounding (with corrections table taking precedence)
        moq = self.moq_handler.get_effective_moq(product.sku, product.moq)
        moq_increment = self.moq_handler.get_effective_increment(product.sku, product.moq_increment)
        buy_units_final = self.moq_handler.round_up_to_moq(buy_units_raw, moq, moq_increment)

        # Back-calculate sell-unit equivalent
        sell_units_final = math.ceil(buy_units_final * conversion_factor)

        # Days supply after order
        days_after = (current_stock + sell_units_final) / burn_rate if burn_rate > 0 else 0

        # Cost estimate
        estimated_total: Decimal | None = None
        if product.unit_cost is not None:
            estimated_total = product.unit_cost * Decimal(buy_units_final)

        notes = []
        if moq != product.moq:
            notes.append(f"MOQ corrected from {product.moq} to {moq} (override applied)")
        if conversion_factor != 1.0:
            notes.append(f"UOM: {sell_units_needed} sell-units → {buy_units_final} buy-units (factor {conversion_factor:.2f})")

        return ReorderRecommendation(
            sku=product.sku,
            product_name=product.name,
            category=product.category,
            manufacturer_code=product.manufacturer_code,
            current_stock_sell_units=current_stock,
            daily_burn_rate=burn_rate,
            days_supply=days_supply,
            recommended_buy_qty=buy_units_final,
            recommended_buy_qty_sell_units=sell_units_final,
            days_supply_after_order=days_after,
            estimated_unit_cost=product.unit_cost,
            estimated_total_cost=estimated_total,
            preferred_suppliers=self._get_preferred_suppliers(product),
            lead_time_days=product.lead_time_days,
            notes="; ".join(notes),
        )

    def _get_preferred_suppliers(self, product: Product) -> list[str]:
        """
        Return a ranked list of preferred suppliers for this product.
        Phase 1: heuristic based on category and available supplier codes.
        Phase 2: will use live price/availability comparison.
        """
        # Suppliers for which we have an explicit code in the product record
        explicit = []
        codes = product.supplier_codes
        if codes.starman:
            explicit.append("starman")
        if codes.beadsmith:
            explicit.append("beadsmith")
        if codes.allbeads:
            explicit.append("allbeads")
        if codes.rutkovsky:
            explicit.append("rutkovsky")
        if codes.gnb:
            explicit.append("gnb")

        if explicit:
            return explicit

        # Fallback: category-based heuristics
        cat = product.category.lower()
        if "czech" in cat or "superduo" in cat or "miniduo" in cat:
            return ["starman", "allbeads", "rutkovsky", "gnb"]
        if "tool" in cat or "finding" in cat:
            return ["beadsmith"]
        if "miyuki" in cat or "toho" in cat or "seed" in cat:
            return ["beadsmith"]
        return ["beadsmith"]
