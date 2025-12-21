"""Unit tests for safety action primitives.

These tests verify that actions return correct intents without performing side effects.
"""

import pytest

from model.actions.safety import (
    check_safety_conditions,
    safe_logout,
    check_and_logout_if_unsafe,
    friends_nearby,
    logout_with_reason,
    stop_bot,
    handle_failure_limit,
    ensure_safe_state,
)
from model.actions.base import ActionResult
from model.actions.intents import CompositeIntent, LogMessageIntent, LogoutIntent, StopIntent


class MockBot:
    """Mock bot for testing safety functions."""

    def __init__(self, friends_nearby: bool = False):
        self._friends_nearby = friends_nearby

    def friends_nearby(self) -> bool:
        return self._friends_nearby


class TestCheckSafetyConditions:
    """Tests for check_safety_conditions function."""

    def test_returns_none_when_safe(self):
        """Should return None when no safety issues."""
        bot = MockBot(friends_nearby=False)

        result = check_safety_conditions(bot)

        assert result is None

    def test_returns_reason_when_friends_nearby(self):
        """Should return reason when friends detected."""
        bot = MockBot(friends_nearby=True)

        result = check_safety_conditions(bot, logout_on_friends=True)

        assert result is not None
        assert "Friends" in result

    def test_ignores_friends_when_disabled(self):
        """Should not check friends when disabled."""
        bot = MockBot(friends_nearby=True)

        result = check_safety_conditions(bot, logout_on_friends=False)

        assert result is None


class TestSafeLogout:
    """Tests for safe_logout function."""

    def test_returns_safety_outcome(self):
        """Should return safety stop outcome."""
        bot = MockBot()

        result = safe_logout(bot, "Test reason")

        assert result.safety_stopped is True
        assert result.result == ActionResult.SAFETY_STOP

    def test_returns_composite_intent(self):
        """Should return CompositeIntent with log, logout, and stop."""
        bot = MockBot()

        result = safe_logout(bot, "Test reason")

        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, CompositeIntent)
        assert len(intent.intents) == 3
        assert isinstance(intent.intents[0], LogMessageIntent)
        assert isinstance(intent.intents[1], LogoutIntent)
        assert isinstance(intent.intents[2], StopIntent)

    def test_intent_includes_reason(self):
        """Should include reason in intents."""
        bot = MockBot()

        result = safe_logout(bot, "Test reason")

        intent = result.data["intent"]
        assert intent.intents[0].message == "Test reason"
        assert intent.intents[1].reason == "Test reason"


class TestCheckAndLogoutIfUnsafe:
    """Tests for check_and_logout_if_unsafe function."""

    def test_returns_ok_when_safe(self):
        """Should return ok when all conditions pass."""
        bot = MockBot(friends_nearby=False)

        result = check_and_logout_if_unsafe(bot)

        assert result.success is True
        assert result.data["safe"] is True
        assert "intent" not in result.data

    def test_returns_safety_intent_when_friends(self):
        """Should return safety stop with intent when friends nearby."""
        bot = MockBot(friends_nearby=True)

        result = check_and_logout_if_unsafe(bot)

        assert result.safety_stopped is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, CompositeIntent)


class TestFriendsNearby:
    """Tests for friends_nearby function."""

    def test_returns_true_when_friends_nearby(self):
        """Should indicate friends nearby when detected."""
        bot = MockBot(friends_nearby=True)

        result = friends_nearby(bot)

        assert result.success is True
        assert result.data["friends_nearby"] is True

    def test_returns_false_when_no_friends(self):
        """Should indicate no friends when not detected."""
        bot = MockBot(friends_nearby=False)

        result = friends_nearby(bot)

        assert result.success is True
        assert result.data["friends_nearby"] is False

    def test_no_intent_returned(self):
        """Should not return an intent (pure query)."""
        bot = MockBot(friends_nearby=False)

        result = friends_nearby(bot)

        assert "intent" not in result.data


class TestLogoutWithReason:
    """Tests for logout_with_reason function."""

    def test_returns_logout_intent(self):
        """Should return CompositeIntent with log and logout (no stop)."""
        bot = MockBot()

        result = logout_with_reason(bot, "Test reason")

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, CompositeIntent)
        assert len(intent.intents) == 2
        assert isinstance(intent.intents[0], LogMessageIntent)
        assert isinstance(intent.intents[1], LogoutIntent)


class TestStopBot:
    """Tests for stop_bot function."""

    def test_returns_stop_intent(self):
        """Should return CompositeIntent with log and stop (no logout)."""
        bot = MockBot()

        result = stop_bot(bot, "Test reason")

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, CompositeIntent)
        assert len(intent.intents) == 2
        assert isinstance(intent.intents[0], LogMessageIntent)
        assert isinstance(intent.intents[1], StopIntent)


class TestHandleFailureLimit:
    """Tests for handle_failure_limit function."""

    def test_returns_ok_under_limit(self):
        """Should return ok when under limit."""
        bot = MockBot()

        result = handle_failure_limit(bot, failures=3, limit=5)

        assert result.success is True
        assert result.data["exceeded"] is False
        assert "intent" not in result.data

    def test_returns_safety_intent_over_limit(self):
        """Should return safety stop with intent when over limit."""
        bot = MockBot()

        result = handle_failure_limit(bot, failures=6, limit=5)

        assert result.safety_stopped is True
        assert "intent" in result.data

    def test_includes_failure_type_in_reason(self):
        """Should include failure type in message."""
        bot = MockBot()

        result = handle_failure_limit(bot, failures=6, limit=5, failure_type="rock search")

        intent = result.data["intent"]
        assert "rock search" in intent.intents[0].message


class TestEnsureSafeState:
    """Tests for ensure_safe_state function."""

    def test_returns_ok_when_all_pass(self):
        """Should return ok when all conditions pass."""
        bot = MockBot(friends_nearby=False)

        result = ensure_safe_state(
            bot,
            logout_on_friends=True,
            max_failures=5,
            current_failures=2
        )

        assert result.success is True
        assert result.data["safe"] is True

    def test_returns_safety_intent_on_friends(self):
        """Should return safety stop with intent when friends detected."""
        bot = MockBot(friends_nearby=True)

        result = ensure_safe_state(bot, logout_on_friends=True)

        assert result.safety_stopped is True
        assert "intent" in result.data

    def test_returns_safety_intent_on_failure_limit(self):
        """Should return safety stop with intent when failure limit exceeded."""
        bot = MockBot(friends_nearby=False)

        result = ensure_safe_state(
            bot,
            logout_on_friends=True,
            max_failures=5,
            current_failures=10
        )

        assert result.safety_stopped is True
        assert "intent" in result.data

    def test_skips_failure_check_when_none(self):
        """Should skip failure check when max_failures is None."""
        bot = MockBot(friends_nearby=False)

        result = ensure_safe_state(
            bot,
            logout_on_friends=True,
            max_failures=None,
            current_failures=100  # High but should be ignored
        )

        assert result.success is True
        assert "intent" not in result.data
