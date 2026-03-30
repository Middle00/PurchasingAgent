"""Tests for UOM converter."""

import pytest
from src.utils.uom_converter import UOMConverter


@pytest.fixture
def converter():
    return UOMConverter()


class TestGetConversionFactor:
    def test_explicit_factor_takes_precedence(self, converter):
        # Even with a known category, explicit factor wins
        factor = converter.get_conversion_factor(
            category="Miyuki Seed Beads",
            sell_uom="TU",
            buy_uom="PK",
            explicit_factor=15.0,
        )
        assert factor == 15.0

    def test_miyuki_100g_to_tube(self, converter):
        factor = converter.get_conversion_factor(
            category="Miyuki Seed Beads 11/0",
            sell_uom="TU",
            buy_uom="PK",
        )
        assert abs(factor - 11.76) < 0.01

    def test_toho_100g_to_tube(self, converter):
        factor = converter.get_conversion_factor(
            category="Toho 11/0 Seed Beads",
            sell_uom="TU",
            buy_uom="PK",
        )
        assert abs(factor - 11.76) < 0.01

    def test_same_uom_returns_1(self, converter):
        factor = converter.get_conversion_factor(
            category="Tools",
            sell_uom="EA",
            buy_uom="EA",
        )
        assert factor == 1.0

    def test_unknown_category_returns_1(self, converter):
        factor = converter.get_conversion_factor(
            category="Mystery Product XYZ",
            sell_uom="TU",
            buy_uom="PK",
        )
        assert factor == 1.0

    def test_czech_bead_ea_to_ea(self, converter):
        factor = converter.get_conversion_factor(
            category="Czech SuperDuo Beads",
            sell_uom="EA",
            buy_uom="EA",
        )
        assert factor == 1.0


class TestBuyUnitsNeeded:
    def test_miyuki_100g_packs_needed(self, converter):
        # Need 100 tubes, each pack makes 11.76 tubes → ceil(100/11.76) = 9
        buy = converter.buy_units_needed(
            sell_units_needed=100,
            category="Miyuki 11/0",
            sell_uom="TU",
            buy_uom="PK",
        )
        assert buy == 9  # ceil(100/11.76) = ceil(8.503) = 9

    def test_no_conversion_needed(self, converter):
        buy = converter.buy_units_needed(
            sell_units_needed=50,
            category="Tools",
            sell_uom="EA",
            buy_uom="EA",
        )
        assert buy == 50

    def test_partial_pack_rounds_up(self, converter):
        # Need 12 tubes from 100g packs (factor 11.76): ceil(12/11.76) = 2
        buy = converter.buy_units_needed(
            sell_units_needed=12,
            category="Miyuki Seed Beads",
            sell_uom="TU",
            buy_uom="PK",
        )
        assert buy == 2

    def test_explicit_factor_used(self, converter):
        # Explicit: 1 pack → 20 units
        buy = converter.buy_units_needed(
            sell_units_needed=45,
            category="Custom Product",
            sell_uom="EA",
            buy_uom="PK",
            explicit_factor=20.0,
        )
        assert buy == 3  # ceil(45/20) = 3


class TestSellUnitsFromBuy:
    def test_miyuki_sell_units(self, converter):
        sell = converter.sell_units_from_buy(
            buy_units=2,
            category="Miyuki 11/0",
            sell_uom="TU",
            buy_uom="PK",
        )
        assert sell == 23  # floor(2 * 11.76) = floor(23.52) = 23

    def test_no_conversion(self, converter):
        sell = converter.sell_units_from_buy(
            buy_units=10,
            category="Tools",
            sell_uom="EA",
            buy_uom="EA",
        )
        assert sell == 10
