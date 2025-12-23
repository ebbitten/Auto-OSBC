"""Tests for window launching and confirmation actions."""

import pytest
from unittest.mock import MagicMock, patch

from model.actions.window import (
    find_window,
    wait_for_window,
    prepare_launch_osbc,
    prepare_launch_runelite,
    confirm_window_exists,
)
from model.actions.intents import LaunchIntent


class TestFindWindow:
    """Tests for find_window function."""

    def test_find_window_partial_match(self):
        """Find window with partial title match."""
        mock_window = MagicMock()
        mock_window.title = "RuneLite - player123"

        with patch("model.actions.window.pywinctl.getAllWindows", return_value=[mock_window]):
            result = find_window("RuneLite")
            assert result == mock_window

    def test_find_window_exact_match(self):
        """Find window with exact title match."""
        mock_window = MagicMock()
        mock_window.title = "RuneLite"

        with patch("model.actions.window.pywinctl.getAllWindows", return_value=[mock_window]):
            result = find_window("RuneLite", exact=True)
            assert result == mock_window

    def test_find_window_exact_match_fails_on_partial(self):
        """Exact match fails when title has extra text."""
        mock_window = MagicMock()
        mock_window.title = "RuneLite - player123"

        with patch("model.actions.window.pywinctl.getAllWindows", return_value=[mock_window]):
            result = find_window("RuneLite", exact=True)
            assert result is None

    def test_find_window_not_found(self):
        """Return None when window not found."""
        mock_window = MagicMock()
        mock_window.title = "Some Other Window"

        with patch("model.actions.window.pywinctl.getAllWindows", return_value=[mock_window]):
            result = find_window("RuneLite")
            assert result is None

    def test_find_window_case_insensitive(self):
        """Partial match is case insensitive."""
        mock_window = MagicMock()
        mock_window.title = "RUNELITE"

        with patch("model.actions.window.pywinctl.getAllWindows", return_value=[mock_window]):
            result = find_window("runelite")
            assert result == mock_window


class TestWaitForWindow:
    """Tests for wait_for_window function."""

    def test_wait_for_window_found_immediately(self):
        """Return success when window found immediately."""
        mock_window = MagicMock()
        mock_window.title = "RuneLite"

        with patch("model.actions.window.find_window", return_value=mock_window):
            result = wait_for_window("RuneLite", timeout=5.0)

            assert result.success is True
            assert "found" in result.message.lower()
            assert result.data["window_title"] == "RuneLite"

    def test_wait_for_window_timeout(self):
        """Return timeout when window not found within timeout."""
        with patch("model.actions.window.find_window", return_value=None):
            result = wait_for_window("RuneLite", timeout=0.1, poll_interval=0.05)

            assert result.timed_out is True
            assert "not found" in result.message.lower()

    def test_wait_for_window_found_after_delay(self):
        """Return success when window appears after a delay."""
        mock_window = MagicMock()
        mock_window.title = "RuneLite"

        call_count = 0

        def delayed_find(pattern, exact=False):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                return mock_window
            return None

        with patch("model.actions.window.find_window", side_effect=delayed_find):
            result = wait_for_window("RuneLite", timeout=5.0, poll_interval=0.05)

            assert result.success is True
            assert call_count >= 3


class TestPrepareLaunchOsbc:
    """Tests for prepare_launch_osbc function (action/confirmation pattern)."""

    def test_prepare_launch_osbc_returns_intent(self):
        """Return LaunchIntent when executable is found."""
        with patch("pathlib.Path.exists", return_value=True):
            result = prepare_launch_osbc()

            assert result.success is True
            assert "intent" in result.data
            intent = result.data["intent"]
            assert isinstance(intent, LaunchIntent)
            assert intent.expected_window == "OS Bot"
            assert "osbc" in intent.command[0].lower()
            assert "gui" in intent.command

    def test_prepare_launch_osbc_executable_not_found(self):
        """Return failure when osbc executable not found."""
        with patch("pathlib.Path.exists", return_value=False):
            result = prepare_launch_osbc()

            assert result.failed is True
            assert "could not find" in result.message.lower()

    def test_prepare_launch_osbc_custom_timeout(self):
        """Custom timeout is passed to LaunchIntent."""
        with patch("pathlib.Path.exists", return_value=True):
            result = prepare_launch_osbc(timeout=60.0)

            assert result.success is True
            intent = result.data["intent"]
            assert intent.timeout == 60.0


class TestPrepareLaunchRunelite:
    """Tests for prepare_launch_runelite function (action/confirmation pattern)."""

    def test_prepare_launch_runelite_returns_intent(self):
        """Return LaunchIntent when executable is found."""
        with patch("os.path.exists", return_value=True):
            result = prepare_launch_runelite(runelite_path="C:\\RuneLite\\RuneLite.exe")

            assert result.success is True
            assert "intent" in result.data
            intent = result.data["intent"]
            assert isinstance(intent, LaunchIntent)
            assert intent.expected_window == "RuneLite"
            assert intent.command == ["C:\\RuneLite\\RuneLite.exe"]

    def test_prepare_launch_runelite_not_found(self):
        """Return failure when RuneLite executable not found."""
        with patch("os.path.exists", return_value=False):
            result = prepare_launch_runelite()

            assert result.failed is True
            assert "could not find" in result.message.lower()

    def test_prepare_launch_runelite_auto_detect(self):
        """Auto-detect RuneLite from common locations."""
        expanded_path = "C:\\Users\\Test\\AppData\\Local\\RuneLite\\RuneLite.exe"

        def mock_expandvars(path):
            if "%LOCALAPPDATA%" in path:
                return path.replace("%LOCALAPPDATA%", "C:\\Users\\Test\\AppData\\Local")
            return path

        def mock_exists(path):
            return path == expanded_path

        with patch("os.path.expandvars", side_effect=mock_expandvars):
            with patch("os.path.exists", side_effect=mock_exists):
                result = prepare_launch_runelite()

                assert result.success is True
                intent = result.data["intent"]
                assert "RuneLite.exe" in intent.command[0]


class TestConfirmWindowExists:
    """Tests for confirm_window_exists function."""

    def test_confirm_window_exists_found(self):
        """Return success when window exists."""
        mock_window = MagicMock()
        mock_window.title = "OS Bot COLOR"

        with patch("model.actions.window.find_window", return_value=mock_window):
            result = confirm_window_exists("OS Bot")

            assert result.success is True
            assert result.data["window_title"] == "OS Bot COLOR"

    def test_confirm_window_exists_not_found(self):
        """Return failure when window doesn't exist."""
        with patch("model.actions.window.find_window", return_value=None):
            result = confirm_window_exists("OS Bot")

            assert result.failed is True
            assert "not found" in result.message.lower()
