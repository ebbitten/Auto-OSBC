"""E2E tests for full launch-to-login flow.

These tests verify the complete workflow from launching OSBC through
to a fully logged-in game state.

WARNING: These tests WILL launch OSBC and RuneLite windows!
They are marked with @pytest.mark.launch to prevent accidental execution.

To run these tests explicitly:
    pytest tests/e2e/test_launch_login.py -m launch -v

To run all E2E tests EXCEPT launch tests:
    pytest tests/e2e/ -m "not launch" -v
"""

import time
import pytest
import pywinctl
from dotenv import load_dotenv
import os

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

load_dotenv()

from model.actions.go_action import go
from model.actions.base import ActionOutcome
from model.system_state import SystemState, SystemStateDetector

# Mark all tests in this module as "launch" tests that actually start OSBC
pytestmark = pytest.mark.launch


def _get_bot_character_name() -> str:
    """Get the bot's character name from environment."""
    return os.getenv("OSBC_USERNAME", "")


def _close_all_bot_windows():
    """Close all RuneLite windows that belong to the bot."""
    bot_char = _get_bot_character_name()
    windows = pywinctl.getWindowsWithTitle("RuneLite")

    for w in windows:
        # Only close bot's windows (login screen or bot's character)
        if w.title == "RuneLite" or w.title == f"RuneLite - {bot_char}":
            try:
                w.close()
            except Exception:
                pass

    # Wait for windows to close
    time.sleep(2)


def _count_bot_windows() -> int:
    """Count RuneLite windows belonging to the bot."""
    bot_char = _get_bot_character_name()
    windows = pywinctl.getWindowsWithTitle("RuneLite")
    count = 0
    for w in windows:
        if w.title == "RuneLite" or w.title == f"RuneLite - {bot_char}":
            count += 1
    return count


class TestFullLaunchToLoginFlow:
    """Test the complete launch-to-login flow."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure clean state before and after tests."""
        # Record initial state
        initial_windows = _count_bot_windows()

        yield

        # Cleanup: If we created windows, close them
        # (unless they were there before)
        current_windows = _count_bot_windows()
        if current_windows > initial_windows:
            _close_all_bot_windows()

    def test_go_from_nothing_to_logged_in(self):
        """Test full flow: no windows -> logged in game.

        This is the main E2E test that verifies:
        1. OSBC is launched if needed
        2. RuneLite is launched from OSBC
        3. Window is positioned correctly (FancyZones)
        4. Login credentials are entered
        5. Game reaches logged-in state
        """
        # Close any existing bot windows to start fresh
        _close_all_bot_windows()

        # Verify we're starting from clean state
        assert _count_bot_windows() == 0, "Expected no bot windows at start"

        # Run the full go flow
        result = go(
            force_restart=False,  # We already closed windows
            skip_login=False,     # Full login
            timeout=180.0,        # 3 minutes should be plenty
        )

        # Verify success
        assert result.success, f"go() failed: {result.message}"

        # Verify we have a RuneLite window
        assert _count_bot_windows() >= 1, "Expected at least one bot window after go()"

        # Verify we're logged in
        detector = SystemStateDetector()
        state = detector.detect()
        assert state == SystemState.LOGGED_IN, f"Expected LOGGED_IN, got {state.name}"

    def test_go_from_login_screen(self):
        """Test flow when already at login screen.

        If RuneLite is already open at login screen, go() should just
        enter credentials and log in.
        """
        # First, get to login screen using skip_login
        _close_all_bot_windows()

        result = go(
            skip_login=True,  # Stop at login screen
            timeout=120.0,
        )

        if not result.success:
            pytest.skip(f"Could not get to login screen: {result.message}")

        # Verify we're at login screen
        detector = SystemStateDetector()
        state = detector.detect()
        if state not in [SystemState.RUNELITE_LOGIN, SystemState.RUNELITE_WELCOME]:
            pytest.skip(f"Not at login screen (state: {state.name})")

        # Now run go() again to complete login
        result = go(
            skip_login=False,
            timeout=60.0,  # Should be faster since window is already open
        )

        assert result.success, f"go() failed from login screen: {result.message}"

        # Verify logged in
        state = detector.detect()
        assert state == SystemState.LOGGED_IN, f"Expected LOGGED_IN, got {state.name}"

    def test_go_skip_login_stops_at_login_screen(self):
        """Test that skip_login=True stops at the login screen."""
        _close_all_bot_windows()

        result = go(
            skip_login=True,
            timeout=120.0,
        )

        assert result.success, f"go(skip_login=True) failed: {result.message}"

        # Should be at login or welcome screen, NOT logged in
        detector = SystemStateDetector()
        state = detector.detect()
        assert state in [
            SystemState.RUNELITE_LOGIN,
            SystemState.RUNELITE_WELCOME,
        ], f"Expected login/welcome screen, got {state.name}"

    def test_go_positions_window_correctly(self):
        """Test that go() positions the window in the FancyZones position."""
        from utilities.machine_config import get_machine_config

        _close_all_bot_windows()

        result = go(
            skip_login=True,  # Just need window positioned
            timeout=120.0,
        )

        if not result.success:
            pytest.skip(f"go() failed: {result.message}")

        # Check window position
        config = get_machine_config()
        expected_pos = config.get_snapped_position()
        expected_size = config.get_window_target_size()

        if expected_pos is None:
            pytest.skip("No snapped_position configured for this machine")

        # Find the bot's window
        bot_char = _get_bot_character_name()
        windows = pywinctl.getWindowsWithTitle("RuneLite")
        bot_window = None
        for w in windows:
            if w.title == "RuneLite" or w.title == f"RuneLite - {bot_char}":
                bot_window = w
                break

        assert bot_window is not None, "Bot window not found"

        # Allow some tolerance for window positioning
        tolerance = 10
        assert abs(bot_window.left - expected_pos[0]) <= tolerance, \
            f"Window X position {bot_window.left} != expected {expected_pos[0]}"
        assert abs(bot_window.top - expected_pos[1]) <= tolerance, \
            f"Window Y position {bot_window.top} != expected {expected_pos[1]}"
        assert abs(bot_window.width - expected_size[0]) <= tolerance, \
            f"Window width {bot_window.width} != expected {expected_size[0]}"
        assert abs(bot_window.height - expected_size[1]) <= tolerance, \
            f"Window height {bot_window.height} != expected {expected_size[1]}"


class TestGoIdempotency:
    """Test that go() is idempotent and handles existing states correctly."""

    def test_go_when_already_logged_in(self):
        """Test that go() returns quickly if already logged in."""
        detector = SystemStateDetector()
        state = detector.detect()

        if state != SystemState.LOGGED_IN:
            pytest.skip("Not currently logged in - run full flow test first")

        start = time.time()
        result = go(timeout=30.0)
        elapsed = time.time() - start

        assert result.success, f"go() failed when already logged in: {result.message}"
        assert elapsed < 5.0, f"go() took {elapsed:.1f}s when already logged in (should be instant)"

    def test_go_does_not_open_duplicate_windows(self):
        """Test that go() doesn't open multiple RuneLite windows."""
        initial_count = _count_bot_windows()

        # Run go() multiple times
        for i in range(3):
            result = go(skip_login=True, timeout=60.0)
            if not result.success:
                pytest.skip(f"go() failed on iteration {i}: {result.message}")
            time.sleep(1)

        final_count = _count_bot_windows()

        # Should not have more than one bot window
        assert final_count <= max(1, initial_count), \
            f"go() created duplicate windows: {initial_count} -> {final_count}"
