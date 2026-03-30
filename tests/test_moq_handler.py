"""Tests for MOQ handler."""

import json
import pytest
from pathlib import Path

from src.utils.moq_handler import MOQHandler


@pytest.fixture
def tmp_corrections(tmp_path):
    """Return a corrections file path in a temp directory."""
    return str(tmp_path / "moq_corrections.json")


@pytest.fixture
def handler(tmp_corrections):
    return MOQHandler(corrections_path=tmp_corrections)


@pytest.fixture
def handler_with_corrections(tmp_corrections):
    """Handler with pre-existing corrections."""
    corrections = {
        "SKU-BAD": {"moq": 12, "increment": 12, "note": "BQ says 72 but really 12"},
        "SKU-INC": {"moq": 6, "increment": 6, "note": "Different increment"},
    }
    Path(tmp_corrections).parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_corrections, "w") as f:
        json.dump(corrections, f)
    return MOQHandler(corrections_path=tmp_corrections)


class TestRoundUpToMOQ:
    def test_quantity_below_moq_returns_moq(self, handler):
        assert handler.round_up_to_moq(5, moq=12, increment=12) == 12

    def test_quantity_equals_moq(self, handler):
        assert handler.round_up_to_moq(12, moq=12, increment=12) == 12

    def test_quantity_above_moq_rounds_up(self, handler):
        # Need 20, moq=12, inc=12 → 24 (2x12)
        assert handler.round_up_to_moq(20, moq=12, increment=12) == 24

    def test_quantity_exactly_two_moqs(self, handler):
        assert handler.round_up_to_moq(24, moq=12, increment=12) == 24

    def test_quantity_25_moq_12(self, handler):
        # Need 25 with moq=12 → 36 (3x12)
        assert handler.round_up_to_moq(25, moq=12, increment=12) == 36

    def test_zero_quantity_returns_moq(self, handler):
        assert handler.round_up_to_moq(0, moq=12, increment=12) == 12

    def test_negative_quantity_returns_moq(self, handler):
        assert handler.round_up_to_moq(-5, moq=12, increment=12) == 12

    def test_moq_6_need_5(self, handler):
        assert handler.round_up_to_moq(5, moq=6, increment=6) == 6

    def test_moq_1(self, handler):
        assert handler.round_up_to_moq(7, moq=1, increment=1) == 7

    def test_small_increment(self, handler):
        # moq=10, inc=5: need 17 → 10 + ceil((17-10)/5)*5 = 10 + 10 = 20
        assert handler.round_up_to_moq(17, moq=10, increment=5) == 20

    def test_increment_defaults_to_moq_when_none(self, handler):
        assert handler.round_up_to_moq(20, moq=12, increment=None) == 24


class TestGetEffectiveMOQ:
    def test_no_correction_returns_bq_value(self, handler):
        assert handler.get_effective_moq("SKU-UNKNOWN", 72) == 72

    def test_correction_overrides_bq(self, handler_with_corrections):
        assert handler_with_corrections.get_effective_moq("SKU-BAD", 72) == 12

    def test_correction_increment(self, handler_with_corrections):
        assert handler_with_corrections.get_effective_increment("SKU-INC", 12) == 6


class TestLogCorrection:
    def test_log_and_retrieve(self, handler):
        handler.log_correction("SKU-NEW", corrected_moq=24, corrected_increment=24, note="Test")
        assert handler.get_effective_moq("SKU-NEW", 100) == 24
        assert handler.get_effective_increment("SKU-NEW", 100) == 24

    def test_correction_persists_to_file(self, tmp_corrections, handler):
        handler.log_correction("SKU-PERSIST", corrected_moq=6)
        # Load a new handler from the same file
        handler2 = MOQHandler(corrections_path=tmp_corrections)
        assert handler2.get_effective_moq("SKU-PERSIST", 72) == 6

    def test_remove_correction(self, handler_with_corrections):
        removed = handler_with_corrections.remove_correction("SKU-BAD")
        assert removed is True
        # Now falls back to BQ value
        assert handler_with_corrections.get_effective_moq("SKU-BAD", 72) == 72

    def test_remove_nonexistent(self, handler):
        assert handler.remove_correction("DOES-NOT-EXIST") is False

    def test_list_corrections(self, handler_with_corrections):
        corrections = handler_with_corrections.list_corrections()
        assert "SKU-BAD" in corrections
        assert "SKU-INC" in corrections
