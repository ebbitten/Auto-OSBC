"""System state detection for launch and login flows.

Provides a unified view of the current system state across:
- OSBC window (running or not)
- RuneLite window (launcher, game loaded, login state)

This enables the 'go' command to detect where we are and route appropriately.
"""

from enum import Enum, auto
from typing import Optional, Tuple

import pywinctl

from model.actions.base import ActionOutcome


class SystemState(Enum):
    """Possible states of the launch/login system."""

    NO_WINDOWS = auto()  # Nothing running
    OSBC_ONLY = auto()  # OSBC running, no RuneLite
    RUNELITE_LAUNCHER = auto()  # Launcher visible (waiting for game)
    RUNELITE_WELCOME = auto()  # Game loaded, "Existing User" button visible
    RUNELITE_LOGIN = auto()  # Username/password entry screen
    RUNELITE_CLICK_TO_PLAY = auto()  # Post-login, needs click to enter
    RUNELITE_LOGGED_IN = auto()  # Fully in-game (inventory visible)
    RUNELITE_UNKNOWN = auto()  # RuneLite open but state unclear


class SystemStateDetector:
    """Detects the current system state.

    Checks for windows and their states to determine where we are
    in the launch/login process.
    """

    def __init__(self):
        """Initialize the detector."""
        self._osbc_window = None
        self._runelite_window = None

    def detect(self) -> SystemState:
        """Detect the current system state.

        Returns:
            SystemState indicating where we are in the process.
        """
        # Check for windows
        osbc_running, runelite_title = self._check_windows()

        # No windows at all
        if not osbc_running and not runelite_title:
            return SystemState.NO_WINDOWS

        # OSBC running but no RuneLite
        if osbc_running and not runelite_title:
            return SystemState.OSBC_ONLY

        # RuneLite window exists - check its state
        if runelite_title:
            # Check if it's the launcher (not the game)
            if "Launcher" in runelite_title:
                return SystemState.RUNELITE_LAUNCHER

            # Game is loaded - check login state
            return self._detect_login_state()

        return SystemState.RUNELITE_UNKNOWN

    def _check_windows(self) -> Tuple[bool, Optional[str]]:
        """Check for OSBC and RuneLite windows.

        Returns:
            Tuple of (osbc_running, runelite_window_title)
        """
        osbc_running = False
        runelite_title = None

        try:
            windows = pywinctl.getAllWindows()
            for window in windows:
                title = window.title
                if not title:
                    continue

                # Check for OSBC
                if "OS Bot" in title:
                    osbc_running = True
                    self._osbc_window = window

                # Check for RuneLite (Launcher or game)
                if "RuneLite" in title:
                    runelite_title = title
                    self._runelite_window = window

        except Exception:
            pass

        return osbc_running, runelite_title

    def _detect_login_state(self) -> SystemState:
        """Detect the login state when RuneLite game is open.

        Returns:
            SystemState for the current login screen state.
        """
        try:
            from utilities.window import Window
            from model.login.login_screen import LoginScreenDetector, LoginState

            # Create a Window object for detection
            win = Window("RuneLite", padding_top=26, padding_left=0)

            # Use the existing LoginScreenDetector
            detector = LoginScreenDetector(win)
            state_info = detector.detect_state()

            # Map LoginState to SystemState
            state_map = {
                LoginState.LOGGED_IN: SystemState.RUNELITE_LOGGED_IN,
                LoginState.WELCOME_SCREEN: SystemState.RUNELITE_WELCOME,
                LoginState.LOGIN_SCREEN: SystemState.RUNELITE_LOGIN,
                LoginState.CLICK_TO_PLAY: SystemState.RUNELITE_CLICK_TO_PLAY,
                LoginState.UNKNOWN: SystemState.RUNELITE_UNKNOWN,
            }

            return state_map.get(state_info.state, SystemState.RUNELITE_UNKNOWN)

        except Exception:
            return SystemState.RUNELITE_UNKNOWN

    def get_state_description(self, state: SystemState) -> str:
        """Get a human-readable description of a state.

        Args:
            state: The SystemState to describe.

        Returns:
            Human-readable description string.
        """
        descriptions = {
            SystemState.NO_WINDOWS: "No OSBC or RuneLite windows running",
            SystemState.OSBC_ONLY: "OSBC running, waiting to launch RuneLite",
            SystemState.RUNELITE_LAUNCHER: "RuneLite Launcher open, waiting for game to load",
            SystemState.RUNELITE_WELCOME: "On welcome screen (need to click 'Existing User')",
            SystemState.RUNELITE_LOGIN: "On login screen (enter credentials)",
            SystemState.RUNELITE_CLICK_TO_PLAY: "Login complete (click to play)",
            SystemState.RUNELITE_LOGGED_IN: "Fully logged in and ready",
            SystemState.RUNELITE_UNKNOWN: "RuneLite open but state unclear",
        }
        return descriptions.get(state, "Unknown state")
