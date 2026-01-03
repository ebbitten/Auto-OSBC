"""E2E test fixtures and configuration.

Provides fixtures for:
- Window management (finding, focusing, restoring)
- State navigation (getting to specific login states)
- Chaos injection utilities
- Cleanup and reset

Uses BotWindowService for all window detection to ensure we only
interact with the bot's windows, never the user's personal windows.
"""

import time
from typing import Generator, Optional

import pytest
import pywinctl
import pyautogui
from dotenv import load_dotenv

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Load environment variables from .env file for OSBC_USERNAME etc.
load_dotenv()

from model.system_state import SystemState, SystemStateDetector
from utilities.window import Window
from utilities.bot_window_service import get_bot_window_service


# Mark all tests in this directory as e2e
def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring game client")
    config.addinivalue_line("markers", "launch: tests that launch OSBC/RuneLite (use -m launch to run explicitly)")


@pytest.fixture
def detector() -> SystemStateDetector:
    """Provide a fresh SystemStateDetector instance."""
    return SystemStateDetector()


@pytest.fixture
def runelite_window() -> Optional[Window]:
    """Get the bot's RuneLite window if running, or None.

    Uses BotWindowService to ensure we only return the bot's window,
    not the user's personal window.
    """
    service = get_bot_window_service()
    return service.get_bot_window_or_none()


@pytest.fixture
def require_runelite(runelite_window) -> Window:
    """Require bot's RuneLite window to be running.

    This fixture DOES NOT auto-launch OSBC/RuneLite to avoid disrupting the user.
    If the bot's window is not running, the test is skipped.

    To run E2E tests, manually launch the bot's RuneLite window first.
    """
    if runelite_window is not None:
        return runelite_window

    service = get_bot_window_service()
    bot_char = service.get_bot_character()

    # Check if there's ANY RuneLite window
    all_runelite = pywinctl.getWindowsWithTitle("RuneLite")
    if all_runelite:
        # RuneLite is running but it's not the bot's window
        titles = [w.title for w in all_runelite]
        pytest.skip(
            f"RuneLite running but not the bot's window. "
            f"Found: {titles}. Expected 'RuneLite' or 'RuneLite - {bot_char}'"
        )

    # No RuneLite at all - skip (don't auto-launch)
    pytest.skip(
        f"Bot's RuneLite window not running. "
        f"Launch RuneLite manually or run 'osbc go' first."
    )


@pytest.fixture
def current_state(detector) -> SystemState:
    """Get the current system state."""
    return detector.detect()


@pytest.fixture
def at_login_screen(require_runelite, detector) -> Generator[Window, None, None]:
    """Ensure we're at the login screen before test, restore after.

    If at WELCOME, clicks Existing User to get to LOGIN.
    If already at LOGIN, proceeds.
    Otherwise skips the test.
    """
    from model.login.login_screen import LoginScreenDetector

    win = require_runelite
    state = detector.detect()

    # Navigate to login if needed
    if state == SystemState.RUNELITE_WELCOME:
        login_detector = LoginScreenDetector(win)
        button = login_detector.get_existing_user_button_location()
        if button:
            from utilities.mouse import Mouse
            mouse = Mouse()
            win.focus()
            time.sleep(0.3)
            mouse.move_to(button.random_point())
            mouse.click()
            time.sleep(1)
            state = detector.detect()

    if state != SystemState.RUNELITE_LOGIN:
        pytest.skip(f"Cannot get to login screen (current: {state.name})")

    yield win

    # Cleanup: no special cleanup needed for login screen


@pytest.fixture
def cleanup_focus():
    """Restore focus to original window after test."""
    # Record current active window
    original = None
    try:
        active = pywinctl.getActiveWindow()
        if active:
            original = active.title
    except Exception:
        pass

    yield

    # Restore focus
    if original:
        try:
            windows = pywinctl.getWindowsWithTitle(original)
            if windows:
                windows[0].activate()
        except Exception:
            pass


class ChaosInjector:
    """Utility class for injecting chaos into the flow.

    Uses BotWindowService to ensure we only operate on the bot's RuneLite window,
    never the user's personal window.
    """

    def __init__(self, window: Window):
        self.window = window
        self._original_position = None
        self._service = get_bot_window_service()

    def _get_bot_window(self):
        """Get the bot's RuneLite window using BotWindowService."""
        return self._service.find_bot_runelite_window()

    def move_window(self, dx: int = 100, dy: int = 100):
        """Move the bot's window by offset."""
        try:
            win = self._get_bot_window()
            if win:
                self._original_position = (win.left, win.top)
                win.moveTo(win.left + dx, win.top + dy)
                time.sleep(0.2)
        except Exception:
            pass

    def restore_window_position(self):
        """Restore window to original position."""
        if self._original_position:
            try:
                win = self._get_bot_window()
                if win:
                    win.moveTo(*self._original_position)
            except Exception:
                pass

    def minimize_window(self):
        """Minimize the bot's game window."""
        try:
            win = self._get_bot_window()
            if win:
                win.minimize()
                time.sleep(0.3)
        except Exception:
            pass

    def restore_window(self):
        """Restore minimized window."""
        try:
            win = self._get_bot_window()
            if win:
                win.restore()
                win.activate()
                time.sleep(0.3)
        except Exception:
            pass

    def click_elsewhere(self, offset: int = 200):
        """Click outside the target area."""
        try:
            rect = self.window.rectangle()
            # Click outside window bounds
            pyautogui.click(rect.left - offset, rect.top + rect.height // 2)
            time.sleep(0.2)
        except Exception:
            pass

    def lose_focus(self):
        """Make another window active."""
        try:
            # Try to find and activate a different window
            for win in pywinctl.getAllWindows():
                if win.title and "RuneLite" not in win.title and win.title.strip():
                    win.activate()
                    time.sleep(0.3)
                    return True
        except Exception:
            pass
        return False

    def type_garbage(self, length: int = 5):
        """Type random garbage characters."""
        import random
        import string
        garbage = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        pyautogui.typewrite(garbage, interval=0.02)
        time.sleep(0.2)

    def random_delay(self, min_sec: float = 1.0, max_sec: float = 5.0):
        """Add a random delay."""
        import random
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)


@pytest.fixture
def chaos_injector(require_runelite) -> Generator[ChaosInjector, None, None]:
    """Provide chaos injection utilities with cleanup."""
    injector = ChaosInjector(require_runelite)
    yield injector

    # Cleanup
    injector.restore_window_position()
    injector.restore_window()
    # Re-focus RuneLite
    try:
        require_runelite.focus()
    except Exception:
        pass
