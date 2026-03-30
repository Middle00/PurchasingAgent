"""Tests for the reorder engine using mock data."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.product import Product, SupplierCodes
from src.models.reorder import ReorderRecommendation
from src.services.reorder_engine import ReorderEngine, TARGET_DAYS_SUPPLY


def make_product(**kwargs) -> Product:
    defaults = dict(
        sku="TEST-001",
        name="Test Product",
        category="Miyuki Seed Beads 11/0",
        manufacturer="Miyuki",
        manufacturer_code="401",
        sell_uom="TU",
        buy_uom="PK",
        uom_conversion_factor=Decimal("11.76"),
        moq=1,
        moq_increment=1,
        lead_time_days=14,
        unit_cost=Decimal("5.00"),
        current_stock=20,
        reorder_point=50,
        days_supply=15.0,
        daily_burn_rate=1.33,
    )
    defaults.update(kwargs)
    return Product(**defaults)


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.default_days_supply_threshold = 30
    settings.moq_corrections_path = "/nonexistent/moq_corrections.json"
    return settings


@pytest.fixture
def mock_bq():
    return MagicMock()


@pytest.fixture
def engine(mock_settings, mock_bq, tmp_path):
    # Point moq corrections to a temp file so no FileNotFoundError
    mock_settings.moq_corrections_path = str(tmp_path / "moq.json")
    return ReorderEngine(mock_settings, mock_bq)


class TestBuildRecommendation:
    def test_basic_recommendation(self, engine):
        product = make_product()
        rec = engine._build_recommendation(product)

        assert rec is not None
        assert rec.sku == "TEST-001"
        assert rec.product_name == "Test Product"
        assert rec.current_stock_sell_units == 20
        assert rec.daily_burn_rate == pytest.approx(1.33)
        assert rec.days_supply == pytest.approx(15.0)

    def test_buy_qty_covers_target_days(self, engine):
        # burn=1.33/day, current=20, target=60 days
        # need = ceil(1.33*60) - 20 = ceil(79.8) - 20 = 80 - 20 = 60 sell-units
        # buy = ceil(60 / 11.76) = ceil(5.1) = 6 packs
        product = make_product()
        rec = engine._build_recommendation(product)
        assert rec is not None
        assert rec.recommended_buy_qty == 6

    def test_days_supply_after_order_exceeds_target(self, engine):
        product = make_product()
        rec = engine._build_recommendation(product)
        assert rec is not None
        assert rec.days_supply_after_order >= TARGET_DAYS_SUPPLY

    def test_no_burn_rate_returns_none(self, engine):
        product = make_product(daily_burn_rate=None)
        rec = engine._build_recommendation(product)
        assert rec is None

    def test_zero_burn_rate_returns_none(self, engine):
        product = make_product(daily_burn_rate=0.0)
        rec = engine._build_recommendation(product)
        assert rec is None

    def test_cost_estimate_calculated(self, engine):
        product = make_product(unit_cost=Decimal("5.00"))
        rec = engine._build_recommendation(product)
        assert rec is not None
        assert rec.estimated_unit_cost == Decimal("5.00")
        assert rec.estimated_total_cost == rec.estimated_unit_cost * rec.recommended_buy_qty

    def test_no_cost_when_unit_cost_missing(self, engine):
        product = make_product(unit_cost=None)
        rec = engine._build_recommendation(product)
        assert rec is not None
        assert rec.estimated_total_cost is None


class TestPreferredSuppliers:
    def test_explicit_supplier_codes_used(self, engine):
        product = make_product(
            supplier_codes=SupplierCodes(beadsmith="11-9401", starman="11/0-401")
        )
        suppliers = engine._get_preferred_suppliers(product)
        # starman listed first in the implementation
        assert "starman" in suppliers
        assert "beadsmith" in suppliers

    def test_category_fallback_for_seed_beads(self, engine):
        product = make_product(category="Miyuki 11/0 Seed Beads", supplier_codes=SupplierCodes())
        suppliers = engine._get_preferred_suppliers(product)
        assert "beadsmith" in suppliers

    def test_category_fallback_for_czech(self, engine):
        product = make_product(category="Czech SuperDuo Beads", supplier_codes=SupplierCodes())
        suppliers = engine._get_preferred_suppliers(product)
        assert "starman" in suppliers


class TestGenerateRecommendations:
    def test_returns_sorted_by_days_supply(self, engine, mock_bq):
        products = [
            make_product(sku="A", days_supply=25.0, daily_burn_rate=2.0, current_stock=50),
            make_product(sku="B", days_supply=5.0, daily_burn_rate=2.0, current_stock=10),
            make_product(sku="C", days_supply=15.0, daily_burn_rate=2.0, current_stock=30),
        ]
        mock_bq.get_items_below_threshold.return_value = products
        recs = engine.generate_recommendations()
        days = [r.days_supply for r in recs]
        assert days == sorted(days)

    def test_empty_when_no_items(self, engine, mock_bq):
        mock_bq.get_items_below_threshold.return_value = []
        recs = engine.generate_recommendations()
        assert recs == []
