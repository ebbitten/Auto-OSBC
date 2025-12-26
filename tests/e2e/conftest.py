"""E2E test fixtures and configuration.

Provides fixtures for:
- Window management (finding, focusing, restoring)
- State navigation (getting to specific login states)
- Chaos injection utilities
- Cleanup and reset
"""

import time
from typing import Generator, Optional

import pytest
import pywinctl
import pyautogui

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from model.system_state import SystemState, SystemStateDetector
from utilities.window import Window


# Mark all tests in this directory as e2e
def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring game client")


@pytest.fixture
def detector() -> SystemStateDetector:
    """Provide a fresh SystemStateDetector instance."""
    return SystemStateDetector()


@pytest.fixture
def runelite_window() -> Optional[Window]:
    """Get RuneLite window if running, or None."""
    try:
        win = Window("RuneLite", padding_top=26, padding_left=0)
        _ = win.rectangle()  # Verify it exists
        return win
    except Exception:
        return None


@pytest.fixture
def require_runelite(runelite_window) -> Window:
    """Require RuneLite to be running, skip test if not."""
    if runelite_window is None:
        pytest.skip("RuneLite not running")
    return runelite_window


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
    """Utility class for injecting chaos into the flow."""

    def __init__(self, window: Window):
        self.window = window
        self._original_position = None

    def move_window(self, dx: int = 100, dy: int = 100):
        """Move the window by offset."""
        try:
            windows = pywinctl.getWindowsWithTitle(self.window.title)
            if windows:
                win = windows[0]
                self._original_position = (win.left, win.top)
                win.moveTo(win.left + dx, win.top + dy)
                time.sleep(0.2)
        except Exception:
            pass

    def restore_window_position(self):
        """Restore window to original position."""
        if self._original_position:
            try:
                windows = pywinctl.getWindowsWithTitle(self.window.title)
                if windows:
                    windows[0].moveTo(*self._original_position)
            except Exception:
                pass

    def minimize_window(self):
        """Minimize the game window."""
        try:
            windows = pywinctl.getWindowsWithTitle(self.window.title)
            if windows:
                windows[0].minimize()
                time.sleep(0.3)
        except Exception:
            pass

    def restore_window(self):
        """Restore minimized window."""
        try:
            windows = pywinctl.getWindowsWithTitle(self.window.title)
            if windows:
                windows[0].restore()
                windows[0].activate()
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
