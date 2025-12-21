"""Unit tests for actions base module."""

import pytest

from model.actions.base import ActionOutcome, ActionResult


class TestActionResult:
    """Tests for ActionResult enum."""

    def test_all_result_types_exist(self):
        """Verify all expected result types are defined."""
        assert ActionResult.SUCCESS
        assert ActionResult.FAILED
        assert ActionResult.TIMEOUT
        assert ActionResult.SAFETY_STOP
        assert ActionResult.SKIPPED


class TestActionOutcome:
    """Tests for ActionOutcome dataclass."""

    def test_success_outcome(self):
        """Test creating a success outcome."""
        outcome = ActionOutcome.ok("Clicked rock")

        assert outcome.success is True
        assert outcome.failed is False
        assert outcome.result == ActionResult.SUCCESS
        assert outcome.message == "Clicked rock"

    def test_failed_outcome(self):
        """Test creating a failed outcome."""
        outcome = ActionOutcome.fail("No rocks found")

        assert outcome.failed is True
        assert outcome.success is False
        assert outcome.result == ActionResult.FAILED

    def test_timeout_outcome(self):
        """Test creating a timeout outcome."""
        outcome = ActionOutcome.timeout("Waited 30 seconds")

        assert outcome.timed_out is True
        assert outcome.success is False

    def test_safety_outcome(self):
        """Test creating a safety stop outcome."""
        outcome = ActionOutcome.safety("Friends nearby")

        assert outcome.safety_stopped is True
        assert outcome.success is False

    def test_skipped_outcome(self):
        """Test creating a skipped outcome."""
        outcome = ActionOutcome.skip("Inventory not full")

        assert outcome.skipped is True
        assert outcome.success is False

    def test_outcome_with_data(self):
        """Test creating an outcome with additional data."""
        outcome = ActionOutcome.ok("Found objects", count=5, nearest_x=100)

        assert outcome.data["count"] == 5
        assert outcome.data["nearest_x"] == 100

    def test_outcome_string_representation(self):
        """Test string representation for logging."""
        outcome = ActionOutcome.ok("All good")

        assert "[SUCCESS]" in str(outcome)
        assert "All good" in str(outcome)

    def test_default_message(self):
        """Test default messages for factory methods."""
        assert "Success" in ActionOutcome.ok().message
        assert "Failed" in ActionOutcome.fail().message
        assert "Timed out" in ActionOutcome.timeout().message
