"""Centralized service for bot window detection and management.

This service ensures the bot only interacts with its own windows,
never the user's personal RuneLite windows.

Usage:
    from utilities.bot_window_service import get_bot_window_service

    service = get_bot_window_service()
    if service.is_bot_window_open():
        window = service.get_bot_window()
"""

import os
from typing import Optional, List, Tuple

import pywinctl
from dotenv import load_dotenv

# Load .env at module import to ensure OSBC_USERNAME is available
load_dotenv()


class BotWindowService:
    """Centralized service for bot window detection and management.

    This is a singleton service that:
    1. Knows which window belongs to the bot (via OSBC_USERNAME from .env)
    2. Provides a single source of truth for window detection
    3. Never returns or interacts with the user's personal windows

    Window Title Patterns:
    - "RuneLite" (exact) = Login screen, belongs to bot
    - "RuneLite - {bot_character}" = Logged in as bot
    - "RuneLite - {other_character}" = User's personal window, DO NOT TOUCH
    - "OS Bot COLOR" = OSBC GUI window
    """

    _instance: Optional["BotWindowService"] = None

    def __init__(self):
        """Initialize the service. Use get_bot_window_service() instead."""
        self._bot_character: Optional[str] = os.getenv("OSBC_USERNAME")

    @classmethod
    def get_instance(cls) -> "BotWindowService":
        """Get the singleton instance of BotWindowService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        cls._instance = None

    # -------------------------------------------------------------------------
    # Character Management
    # -------------------------------------------------------------------------

    def get_bot_character(self) -> Optional[str]:
        """Get the bot's character name from environment.

        Returns:
            Character name from OSBC_USERNAME, or None if not set.
        """
        return self._bot_character

    def set_bot_character(self, character: str) -> None:
        """Override the bot character (useful for testing or multi-bot scenarios).

        Args:
            character: The character name to use.
        """
        self._bot_character = character

    # -------------------------------------------------------------------------
    # Window Identification
    # -------------------------------------------------------------------------

    def is_bot_window(self, window_title: str) -> bool:
        """Check if a window title belongs to the bot.

        Args:
            window_title: The window title to check.

        Returns:
            True if this is the bot's window, False otherwise.

        Window Matching Rules:
        - "RuneLite" (exact match) -> True (login screen, no character yet)
        - "RuneLite - {bot_character}" -> True (logged in as bot)
        - "RuneLite - {other_character}" -> False (user's personal window)
        - "RuneLite Launcher" or other variants -> False
        """
        if not window_title:
            return False

        # Exact match for login screen
        if window_title == "RuneLite":
            return True

        # Check for bot's character
        if self._bot_character:
            expected_title = f"RuneLite - {self._bot_character}"
            if window_title == expected_title:
                return True

        return False

    def is_osbc_window(self, window_title: str) -> bool:
        """Check if a window title is the OSBC GUI.

        Args:
            window_title: The window title to check.

        Returns:
            True if this is the OSBC GUI window.
        """
        return window_title and "OS Bot" in window_title

    def get_character_from_title(self, window_title: str) -> Optional[str]:
        """Extract character name from a RuneLite window title.

        Args:
            window_title: Window title like "RuneLite - characterName"

        Returns:
            Character name if found, None otherwise.
        """
        if window_title and " - " in window_title:
            return window_title.split(" - ", 1)[1].strip()
        return None

    # -------------------------------------------------------------------------
    # Window Discovery
    # -------------------------------------------------------------------------

    def find_bot_runelite_window(self) -> Optional[pywinctl.Window]:
        """Find the bot's RuneLite window.

        Returns:
            The pywinctl Window if found, None otherwise.

        This will return:
        - A window with exact title "RuneLite" (login screen)
        - A window with title "RuneLite - {bot_character}"

        This will NOT return:
        - Windows like "RuneLite - other_character"
        """
        try:
            windows = pywinctl.getWindowsWithTitle("RuneLite")
            for win in windows:
                if self.is_bot_window(win.title):
                    return win
        except Exception:
            pass
        return None

    def find_osbc_window(self) -> Optional[pywinctl.Window]:
        """Find the OSBC GUI window.

        Returns:
            The pywinctl Window if found, None otherwise.
        """
        try:
            windows = pywinctl.getWindowsWithTitle("OS Bot")
            if windows:
                return windows[0]
        except Exception:
            pass
        return None

    def find_all_bot_windows(self) -> List[pywinctl.Window]:
        """Find all RuneLite windows belonging to the bot.

        Returns:
            List of pywinctl Windows that belong to the bot.
        """
        result = []
        try:
            windows = pywinctl.getWindowsWithTitle("RuneLite")
            for win in windows:
                if self.is_bot_window(win.title):
                    result.append(win)
        except Exception:
            pass
        return result

    def check_windows_status(self) -> Tuple[bool, bool, Optional[str]]:
        """Check the status of OSBC and RuneLite windows.

        Returns:
            Tuple of (osbc_running, bot_runelite_running, bot_window_title)
        """
        osbc_running = self.find_osbc_window() is not None
        bot_window = self.find_bot_runelite_window()
        bot_runelite_running = bot_window is not None
        bot_window_title = bot_window.title if bot_window else None

        return osbc_running, bot_runelite_running, bot_window_title

    # -------------------------------------------------------------------------
    # Window Object Creation
    # -------------------------------------------------------------------------

    def get_bot_window(self) -> "Window":
        """Get a Window object for the bot's RuneLite window.

        Returns:
            Window object configured for the bot's window.

        Raises:
            WindowNotFoundError: If no bot window is found.
        """
        from utilities.window import Window, WindowInitializationError

        bot_win = self.find_bot_runelite_window()
        if bot_win is None:
            raise WindowInitializationError("Bot's RuneLite window not found")

        # Use the exact title to ensure we get the right window
        return Window(bot_win.title, padding_top=26, padding_left=0)

    def get_bot_window_or_none(self) -> Optional["Window"]:
        """Get a Window object for the bot's RuneLite window, or None.

        Returns:
            Window object if bot window exists, None otherwise.
        """
        try:
            return self.get_bot_window()
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Window State Checks
    # -------------------------------------------------------------------------

    def is_bot_window_open(self) -> bool:
        """Check if the bot has a RuneLite window open.

        Returns:
            True if bot's window is open, False otherwise.
        """
        return self.find_bot_runelite_window() is not None

    def is_osbc_open(self) -> bool:
        """Check if OSBC GUI is open.

        Returns:
            True if OSBC is open, False otherwise.
        """
        return self.find_osbc_window() is not None

    # -------------------------------------------------------------------------
    # Window Management
    # -------------------------------------------------------------------------

    def close_bot_windows(self) -> int:
        """Close all RuneLite windows belonging to the bot.

        Returns:
            Number of windows closed.
        """
        count = 0
        for win in self.find_all_bot_windows():
            try:
                win.close()
                count += 1
            except Exception:
                pass
        return count

    def position_bot_window(self) -> bool:
        """Position the bot's window to the configured FancyZones location.

        Returns:
            True if window was positioned, False otherwise.
        """
        from utilities.machine_config import get_machine_config

        bot_win = self.find_bot_runelite_window()
        if bot_win is None:
            return False

        config = get_machine_config()
        pos = config.get_snapped_position()
        size = config.get_window_target_size()

        if pos is None:
            # No FancyZones config, use bot zone
            zone = config.get_bot_zone()
            if zone:
                pos = (zone.get("left", 0), 0)

        if pos:
            try:
                bot_win.moveTo(pos[0], pos[1])
                if size:
                    bot_win.resizeTo(size[0], size[1])
                return True
            except Exception:
                pass

        return False


# Module-level convenience function
def get_bot_window_service() -> BotWindowService:
    """Get the singleton BotWindowService instance.

    This is the recommended way to access the service.

    Returns:
        The BotWindowService singleton.
    """
    return BotWindowService.get_instance()
