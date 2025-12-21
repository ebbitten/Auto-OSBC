"""Unit tests for inventory action primitives.

These tests verify that actions return correct intents without performing side effects.
"""

import pytest

from model.actions.inventory import (
    manage_if_full,
    drop_all_items,
    drop_slots,
    is_full,
    count_items,
    has_space,
    wait_for_items,
)
from model.actions.base import ActionResult
from model.actions.intents import DropIntent, DropSlotsIntent, WaitIntent


class MockBot:
    """Mock bot for testing inventory functions."""

    def __init__(self, inventory_count: int = 0, is_full: bool = False):
        self._inventory_count = inventory_count
        self._is_full = is_full

    def is_inventory_full_visual(self) -> bool:
        return self._is_full

    def count_inventory_items_visual(self) -> int:
        return self._inventory_count

    def set_inventory_count(self, count: int):
        self._inventory_count = count
        self._is_full = count >= 28


class TestManageIfFull:
    """Tests for manage_if_full function."""

    def test_skips_when_not_full(self):
        """Should skip if inventory is not full."""
        bot = MockBot(inventory_count=10, is_full=False)

        result = manage_if_full(bot)

        assert result.skipped is True
        assert result.data["dropped"] is False
        assert "intent" not in result.data

    def test_returns_drop_intent_when_full(self):
        """Should return DropIntent when inventory is full."""
        bot = MockBot(inventory_count=28, is_full=True)

        result = manage_if_full(bot)

        assert result.success is True
        assert result.data["dropped"] is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, DropIntent)

    def test_passes_skip_slots_to_intent(self):
        """Should include skip_slots in DropIntent."""
        bot = MockBot(inventory_count=28, is_full=True)
        skip_slots = [0, 1, 2]

        result = manage_if_full(bot, skip_slots=skip_slots)

        intent = result.data["intent"]
        assert intent.skip_slots == skip_slots

    def test_passes_skip_rows_to_intent(self):
        """Should include skip_rows in DropIntent."""
        bot = MockBot(inventory_count=28, is_full=True)

        result = manage_if_full(bot, skip_rows=2)

        intent = result.data["intent"]
        assert intent.skip_rows == 2


class TestDropAllItems:
    """Tests for drop_all_items function."""

    def test_returns_drop_intent(self):
        """Should return DropIntent."""
        bot = MockBot(inventory_count=20, is_full=False)

        result = drop_all_items(bot)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, DropIntent)

    def test_skips_when_empty(self):
        """Should skip if inventory is empty."""
        bot = MockBot(inventory_count=0, is_full=False)

        result = drop_all_items(bot)

        assert result.skipped is True
        assert "intent" not in result.data

    def test_reports_initial_count(self):
        """Should report initial item count."""
        bot = MockBot(inventory_count=15, is_full=False)

        result = drop_all_items(bot)

        assert result.data["initial_count"] == 15


class TestDropSlots:
    """Tests for drop_slots function."""

    def test_returns_drop_slots_intent(self):
        """Should return DropSlotsIntent for specified slots."""
        bot = MockBot(inventory_count=10, is_full=False)
        slots = [5, 10, 15]

        result = drop_slots(bot, slots)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, DropSlotsIntent)
        assert intent.slots == slots

    def test_skips_when_no_slots(self):
        """Should skip if no slots specified."""
        bot = MockBot(inventory_count=10, is_full=False)

        result = drop_slots(bot, [])

        assert result.skipped is True
        assert "intent" not in result.data


class TestIsFull:
    """Tests for is_full function."""

    def test_returns_true_when_full(self):
        """Should return is_full=True when inventory is full."""
        bot = MockBot(inventory_count=28, is_full=True)

        result = is_full(bot)

        assert result.success is True
        assert result.data["is_full"] is True
        assert result.data["count"] == 28

    def test_returns_false_when_not_full(self):
        """Should return is_full=False when inventory is not full."""
        bot = MockBot(inventory_count=10, is_full=False)

        result = is_full(bot)

        assert result.success is True
        assert result.data["is_full"] is False
        assert result.data["count"] == 10

    def test_no_intent_returned(self):
        """Should not return an intent (pure query)."""
        bot = MockBot(inventory_count=10, is_full=False)

        result = is_full(bot)

        assert "intent" not in result.data


class TestCountItems:
    """Tests for count_items function."""

    def test_returns_item_count(self):
        """Should return correct item count."""
        bot = MockBot(inventory_count=15, is_full=False)

        result = count_items(bot)

        assert result.success is True
        assert result.data["count"] == 15
        assert result.data["empty_slots"] == 13
        assert result.data["capacity"] == 28

    def test_no_intent_returned(self):
        """Should not return an intent (pure query)."""
        bot = MockBot(inventory_count=15, is_full=False)

        result = count_items(bot)

        assert "intent" not in result.data


class TestHasSpace:
    """Tests for has_space function."""

    def test_returns_true_when_has_space(self):
        """Should return has_space=True when enough space."""
        bot = MockBot(inventory_count=20, is_full=False)

        result = has_space(bot, required_slots=5)

        assert result.success is True
        assert result.data["has_space"] is True
        assert result.data["empty_slots"] == 8

    def test_returns_false_when_not_enough_space(self):
        """Should return has_space=False when not enough space."""
        bot = MockBot(inventory_count=25, is_full=False)

        result = has_space(bot, required_slots=5)

        assert result.success is True
        assert result.data["has_space"] is False
        assert result.data["empty_slots"] == 3


class TestWaitForItems:
    """Tests for wait_for_items function."""

    def test_returns_wait_intent(self):
        """Should return WaitIntent."""
        bot = MockBot(inventory_count=20, is_full=False)

        result = wait_for_items(bot, target_count=28, timeout_seconds=1.0)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, WaitIntent)
        assert intent.timeout == 1.0

    def test_includes_target_count_in_data(self):
        """Should include target count in result data."""
        bot = MockBot(inventory_count=10, is_full=False)

        result = wait_for_items(bot, target_count=28)

        assert result.data["target_count"] == 28

    def test_wait_condition_checks_inventory(self):
        """WaitIntent condition should check inventory count."""
        bot = MockBot(inventory_count=20, is_full=False)

        result = wait_for_items(bot, target_count=28)

        intent = result.data["intent"]
        # Initially false (20 < 28)
        assert intent.condition() is False
        # After count increases
        bot.set_inventory_count(28)
        assert intent.condition() is True
