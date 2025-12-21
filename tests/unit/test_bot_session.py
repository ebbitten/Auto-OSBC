"""Unit tests for BotSession context manager."""

import time
from unittest.mock import MagicMock, patch

import pytest

from model.bot import BotSession, BotStatus


class MockBot:
    """Mock bot for testing BotSession."""

    def __init__(self):
        self.status = BotStatus.RUNNING
        self.progress = 0
        self.log_messages = []

    def update_progress(self, progress: float):
        self.progress = progress

    def log_msg(self, msg: str):
        self.log_messages.append(msg)


class TestBotSessionBasics:
    """Basic tests for BotSession."""

    def test_session_context_manager(self):
        """Test session can be used as context manager."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            assert session is not None
            assert session.bot is bot

    def test_session_sets_progress_on_exit(self):
        """Test session sets progress to 1.0 on exit."""
        bot = MockBot()

        with BotSession(bot, 1.0):
            pass

        assert bot.progress == 1.0

    def test_session_from_bot_method(self):
        """Test creating session via bot.timed_session()."""
        # This would require a real Bot instance, so we test the class directly
        bot = MockBot()
        session = BotSession(bot, 5.0)

        assert session.duration_seconds == 300  # 5 minutes


class TestBotSessionTiming:
    """Tests for BotSession timing functionality."""

    def test_running_true_when_time_remaining(self):
        """Session should be running when time remains."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            # Should be running at start
            assert session.running is True

    def test_running_false_when_bot_stopped(self):
        """Session should stop when bot status changes."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            bot.status = BotStatus.STOPPED
            assert session.running is False

    def test_elapsed_time_tracking(self):
        """Test elapsed time is tracked correctly."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            # Small delay to ensure elapsed > 0
            time.sleep(0.01)
            assert session.elapsed_seconds > 0
            assert session.elapsed_minutes > 0

    def test_remaining_time_calculation(self):
        """Test remaining time decreases."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            initial_remaining = session.remaining_seconds
            time.sleep(0.01)
            assert session.remaining_seconds <= initial_remaining

    def test_remaining_time_never_negative(self):
        """Remaining time should never be negative."""
        bot = MockBot()
        session = BotSession(bot, 0.0001)  # Very short duration

        with session:
            time.sleep(0.01)  # Wait past duration
            assert session.remaining_seconds >= 0


class TestBotSessionCounters:
    """Tests for BotSession counter functionality."""

    def test_increment_counter(self):
        """Test incrementing a counter."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            result = session.increment("rocks_mined")
            assert result == 1
            assert session.get_count("rocks_mined") == 1

    def test_increment_counter_multiple(self):
        """Test incrementing a counter multiple times."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            session.increment("items")
            session.increment("items")
            session.increment("items", 5)

            assert session.get_count("items") == 7

    def test_get_count_nonexistent(self):
        """Getting nonexistent counter should return 0."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            assert session.get_count("nonexistent") == 0

    def test_multiple_counters(self):
        """Test tracking multiple counters."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            session.increment("rocks")
            session.increment("fish", 3)
            session.increment("logs", 2)

            assert session.get_count("rocks") == 1
            assert session.get_count("fish") == 3
            assert session.get_count("logs") == 2


class TestBotSessionFailureTracking:
    """Tests for BotSession failure tracking."""

    def test_track_failure_under_limit(self):
        """Tracking failures under limit should return False."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            assert session.track_failure("search", limit=5) is False
            assert session.track_failure("search", limit=5) is False

    def test_track_failure_at_limit(self):
        """Tracking failures at limit should still return False."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            for _ in range(5):
                result = session.track_failure("search", limit=5)
            assert result is False  # At limit, not over

    def test_track_failure_over_limit(self):
        """Tracking failures over limit should return True."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            for _ in range(5):
                session.track_failure("search", limit=5)
            # 6th failure exceeds limit of 5
            assert session.track_failure("search", limit=5) is True

    def test_reset_failures(self):
        """Test resetting failure count."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            for _ in range(3):
                session.track_failure("search", limit=5)

            session.reset_failures("search")

            # Should not exceed limit now
            assert session.track_failure("search", limit=5) is False

    def test_multiple_failure_types(self):
        """Test tracking multiple failure types independently."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            # Track different failure types
            for _ in range(6):
                session.track_failure("rocks", limit=5)

            for _ in range(3):
                session.track_failure("fish", limit=5)

            # rocks should exceed, fish should not
            assert session.track_failure("rocks", limit=5) is True
            assert session.track_failure("fish", limit=5) is False


class TestBotSessionLogging:
    """Tests for BotSession logging functionality."""

    def test_log_stats_with_counters(self):
        """Test logging stats when counters exist."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            session.increment("rocks", 5)
            session.increment("fish", 3)
            session.log_stats()

        assert len(bot.log_messages) == 1
        assert "rocks: 5" in bot.log_messages[0]
        assert "fish: 3" in bot.log_messages[0]

    def test_log_stats_empty(self):
        """Test logging stats with no counters."""
        bot = MockBot()

        with BotSession(bot, 1.0) as session:
            session.log_stats()

        # No message logged when no counters
        assert len(bot.log_messages) == 0
