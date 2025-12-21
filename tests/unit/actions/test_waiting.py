"""Unit tests for waiting action primitives.

These tests verify that actions return correct WaitIntents.
The Executor is responsible for actually polling the conditions.
"""

import pytest

from model.actions.waiting import (
    wait_for_idle,
    wait_for_action,
    wait_while_action,
    wait_until,
    wait_for_inventory_change,
)
from model.actions.base import ActionResult
from model.actions.intents import WaitIntent


class MockBot:
    """Mock bot for testing waiting functions."""

    def __init__(self, idle: bool = True, inventory_count: int = 0):
        self._idle = idle
        self._inventory_count = inventory_count
        self.game_state = None

    def is_player_idle_visual(self) -> bool:
        return self._idle

    def count_inventory_items_visual(self) -> int:
        return self._inventory_count

    def set_idle(self, idle: bool):
        self._idle = idle

    def set_inventory_count(self, count: int):
        self._inventory_count = count


class MockGameState:
    """Mock game state for testing action detection."""

    def __init__(self, current_action: str = ""):
        self.current_action = current_action

    def is_player_doing_action(self, action: str) -> bool:
        return self.current_action.lower() == action.lower()


class TestWaitForIdle:
    """Tests for wait_for_idle function."""

    def test_returns_wait_intent(self):
        """Should return WaitIntent."""
        bot = MockBot(idle=True)

        result = wait_for_idle(bot, timeout_seconds=1.0)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, WaitIntent)

    def test_wait_intent_has_correct_timeout(self):
        """Should include timeout in intent."""
        bot = MockBot(idle=True)

        result = wait_for_idle(bot, timeout_seconds=30.0)

        intent = result.data["intent"]
        assert intent.timeout == 30.0

    def test_wait_intent_has_correct_poll_interval(self):
        """Should include poll interval in intent."""
        bot = MockBot(idle=True)

        result = wait_for_idle(bot, poll_interval=0.5)

        intent = result.data["intent"]
        assert intent.poll_interval == 0.5

    def test_condition_checks_idle_state(self):
        """WaitIntent condition should check player idle state."""
        bot = MockBot(idle=False)

        result = wait_for_idle(bot)

        intent = result.data["intent"]
        # Initially false (not idle)
        assert intent.condition() is False
        # After becoming idle
        bot.set_idle(True)
        assert intent.condition() is True

    def test_description_included(self):
        """Should include description in intent."""
        bot = MockBot()

        result = wait_for_idle(bot)

        intent = result.data["intent"]
        assert "idle" in intent.description.lower()


class TestWaitForAction:
    """Tests for wait_for_action function."""

    def test_returns_wait_intent(self):
        """Should return WaitIntent."""
        bot = MockBot(idle=True)

        result = wait_for_action(bot, "Mining", timeout_seconds=1.0)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, WaitIntent)

    def test_includes_action_name_in_data(self):
        """Should include action name in result data."""
        bot = MockBot()

        result = wait_for_action(bot, "Mining")

        assert result.data["action"] == "Mining"

    def test_condition_with_game_state(self):
        """Condition should check game_state when available."""
        bot = MockBot()
        bot.game_state = MockGameState(current_action="Mining")

        result = wait_for_action(bot, "Mining")

        intent = result.data["intent"]
        assert intent.condition() is True

    def test_condition_fallback_when_no_game_state(self):
        """Should use idle detection fallback when no game_state."""
        bot = MockBot(idle=False)  # Not idle = doing something
        bot.game_state = None

        result = wait_for_action(bot, "Mining")

        intent = result.data["intent"]
        assert intent.condition() is True  # Not idle means doing action


class TestWaitWhileAction:
    """Tests for wait_while_action function."""

    def test_returns_wait_intent(self):
        """Should return WaitIntent."""
        bot = MockBot()

        result = wait_while_action(bot, "Mining", timeout_seconds=1.0)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, WaitIntent)

    def test_condition_true_when_action_stops(self):
        """Condition should be true when action stops."""
        bot = MockBot()
        bot.game_state = MockGameState(current_action="")  # Not doing action

        result = wait_while_action(bot, "Mining")

        intent = result.data["intent"]
        assert intent.condition() is True  # Action completed

    def test_condition_false_while_action_continues(self):
        """Condition should be false while action continues."""
        bot = MockBot()
        bot.game_state = MockGameState(current_action="Mining")

        result = wait_while_action(bot, "Mining")

        intent = result.data["intent"]
        assert intent.condition() is False  # Still doing action

    def test_fallback_when_no_game_state(self):
        """Should use idle detection fallback when no game_state."""
        bot = MockBot(idle=True)  # Idle = action finished
        bot.game_state = None

        result = wait_while_action(bot, "Mining")

        intent = result.data["intent"]
        assert intent.condition() is True


class TestWaitUntil:
    """Tests for wait_until function."""

    def test_returns_wait_intent(self):
        """Should return WaitIntent."""
        bot = MockBot()

        result = wait_until(
            bot,
            lambda b: True,
            timeout_seconds=1.0,
            description="always true"
        )

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, WaitIntent)

    def test_condition_wrapped_correctly(self):
        """Wrapped condition should work without bot argument."""
        bot = MockBot()

        result = wait_until(
            bot,
            lambda b: b._idle,  # Access bot state
            timeout_seconds=1.0,
        )

        intent = result.data["intent"]
        # Bot is idle by default
        assert intent.condition() is True
        # After changing state
        bot.set_idle(False)
        assert intent.condition() is False

    def test_condition_handles_exceptions(self):
        """Wrapped condition should return False on exception."""
        bot = MockBot()

        result = wait_until(
            bot,
            lambda b: 1/0,  # Will raise ZeroDivisionError
            timeout_seconds=1.0,
        )

        intent = result.data["intent"]
        # Should return False, not raise
        assert intent.condition() is False

    def test_includes_description(self):
        """Should include description in intent."""
        bot = MockBot()

        result = wait_until(
            bot,
            lambda b: True,
            description="custom description"
        )

        intent = result.data["intent"]
        assert intent.description == "custom description"


class TestWaitForInventoryChange:
    """Tests for wait_for_inventory_change function."""

    def test_returns_wait_intent(self):
        """Should return WaitIntent."""
        bot = MockBot(inventory_count=10)

        result = wait_for_inventory_change(bot, expected_change=1)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, WaitIntent)

    def test_includes_start_count_in_data(self):
        """Should include start count in result data."""
        bot = MockBot(inventory_count=10)

        result = wait_for_inventory_change(bot, expected_change=1)

        assert result.data["start_count"] == 10
        assert result.data["expected_change"] == 1

    def test_condition_detects_increase(self):
        """Condition should detect expected increase."""
        bot = MockBot(inventory_count=10)

        result = wait_for_inventory_change(bot, expected_change=1)

        intent = result.data["intent"]
        # Initially false (count is 10, need 11)
        assert intent.condition() is False
        # After count increases
        bot.set_inventory_count(11)
        assert intent.condition() is True

    def test_condition_detects_decrease(self):
        """Condition should detect expected decrease."""
        bot = MockBot(inventory_count=10)

        result = wait_for_inventory_change(bot, expected_change=-1)

        intent = result.data["intent"]
        # Initially false (count is 10, need 9)
        assert intent.condition() is False
        # After count decreases
        bot.set_inventory_count(9)
        assert intent.condition() is True

    def test_condition_succeeds_when_exceeds_target(self):
        """Condition should succeed when change exceeds expected."""
        bot = MockBot(inventory_count=10)

        result = wait_for_inventory_change(bot, expected_change=1)

        intent = result.data["intent"]
        # Got 3 items instead of 1
        bot.set_inventory_count(13)
        assert intent.condition() is True

    def test_zero_change_immediate_success(self):
        """Zero expected change should succeed immediately."""
        bot = MockBot(inventory_count=10)

        result = wait_for_inventory_change(bot, expected_change=0)

        intent = result.data["intent"]
        assert intent.condition() is True
