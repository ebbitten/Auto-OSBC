"""Tests for OSBC GUI interaction actions."""

import pytest
from unittest.mock import MagicMock, patch

from model.actions.osbc import (
    check_windows_status,
    find_launch_button,
    prepare_click_launch_button,
    confirm_runelite_window,
    confirm_runelite_login_screen,
)
from model.actions.intents import ClickIntent


class TestCheckWindowsStatus:
    """Tests for check_windows_status function."""

    def test_both_windows_running(self):
        """Return status when both OSBC and RuneLite running."""
        mock_osbc = MagicMock()
        mock_osbc.title = "OS Bot COLOR"
        mock_runelite = MagicMock()
        mock_runelite.title = "RuneLite - player123"

        def find_window_mock(title):
            if "OS Bot" in title:
                return mock_osbc
            if "RuneLite" in title:
                return mock_runelite
            return None

        with patch("model.actions.osbc.find_window", side_effect=find_window_mock):
            result = check_windows_status()

            assert result.success is True
            assert result.data["osbc_running"] is True
            assert result.data["runelite_running"] is True
            assert "OS Bot COLOR" in result.message
            assert "RuneLite" in result.message

    def test_only_osbc_running(self):
        """Return status when only OSBC running."""
        mock_osbc = MagicMock()
        mock_osbc.title = "OS Bot COLOR"

        def find_window_mock(title):
            if "OS Bot" in title:
                return mock_osbc
            return None

        with patch("model.actions.osbc.find_window", side_effect=find_window_mock):
            result = check_windows_status()

            assert result.success is True
            assert result.data["osbc_running"] is True
            assert result.data["runelite_running"] is False
            assert "not running" in result.message

    def test_neither_running(self):
        """Return status when neither window running."""
        with patch("model.actions.osbc.find_window", return_value=None):
            result = check_windows_status()

            assert result.success is True
            assert result.data["osbc_running"] is False
            assert result.data["runelite_running"] is False
            assert "OSBC: not running" in result.message
            assert "RuneLite: not running" in result.message


class TestFindLaunchButton:
    """Tests for find_launch_button function."""

    def test_find_launch_button_with_template(self):
        """Find button using template matching."""
        mock_window = MagicMock()
        mock_window.left = 100
        mock_window.top = 100
        mock_window.width = 680
        mock_window.height = 480

        # Mock BOT_IMAGES path to exist
        mock_bot_images = MagicMock()
        mock_actions_path = MagicMock()
        mock_template_path = MagicMock()
        mock_template_path.exists.return_value = True
        mock_actions_path.__truediv__ = MagicMock(return_value=mock_template_path)
        mock_bot_images.__truediv__ = MagicMock(return_value=mock_actions_path)

        with patch("model.actions.osbc.BOT_IMAGES", mock_bot_images):
            with patch("pyautogui.locateOnScreen") as mock_locate:
                mock_location = MagicMock()
                mock_locate.return_value = mock_location
                with patch("pyautogui.center") as mock_center:
                    mock_center.return_value = MagicMock(x=420, y=250)

                    result = find_launch_button(mock_window)

                    assert result == (420, 250)
                    mock_locate.assert_called_once()

    def test_find_launch_button_template_not_found(self):
        """Return None when template file doesn't exist."""
        mock_window = MagicMock()
        mock_window.left = 100
        mock_window.top = 100
        mock_window.width = 680
        mock_window.height = 480

        # Mock template not existing
        mock_bot_images = MagicMock()
        mock_actions_path = MagicMock()
        mock_template_path = MagicMock()
        mock_template_path.exists.return_value = False
        mock_actions_path.__truediv__ = MagicMock(return_value=mock_template_path)
        mock_bot_images.__truediv__ = MagicMock(return_value=mock_actions_path)

        with patch("model.actions.osbc.BOT_IMAGES", mock_bot_images):
            result = find_launch_button(mock_window)

            # No fallback - returns None when template not found
            assert result is None

    def test_find_launch_button_template_match_fails(self):
        """Return None when template matching raises exception."""
        mock_window = MagicMock()
        mock_window.left = 50
        mock_window.top = 50
        mock_window.width = 680
        mock_window.height = 480

        mock_bot_images = MagicMock()
        mock_actions_path = MagicMock()
        mock_template_path = MagicMock()
        mock_template_path.exists.return_value = True
        mock_actions_path.__truediv__ = MagicMock(return_value=mock_template_path)
        mock_bot_images.__truediv__ = MagicMock(return_value=mock_actions_path)

        with patch("model.actions.osbc.BOT_IMAGES", mock_bot_images):
            with patch("pyautogui.locateOnScreen", side_effect=Exception("Match failed")):
                result = find_launch_button(mock_window)

                # No fallback - returns None when template matching fails
                assert result is None


class TestPrepareClickLaunchButton:
    """Tests for prepare_click_launch_button function."""

    def test_prepare_click_launch_button_success(self):
        """Return ClickIntent when OSBC window found."""
        mock_window = MagicMock()
        mock_window.left = 100
        mock_window.top = 100
        mock_window.width = 680
        mock_window.height = 480

        with patch("model.actions.osbc.find_window", return_value=mock_window):
            with patch("model.actions.osbc.find_launch_button", return_value=(420, 250)):
                result = prepare_click_launch_button()

                assert result.success is True
                assert "intent" in result.data
                intent = result.data["intent"]
                assert isinstance(intent, ClickIntent)
                assert intent.point == (420, 250)
                assert intent.speed == "medium"

    def test_prepare_click_launch_button_osbc_not_found(self):
        """Return failure when OSBC window not found."""
        with patch("model.actions.osbc.find_window", return_value=None):
            result = prepare_click_launch_button()

            assert result.failed is True
            assert "not found" in result.message.lower()

    def test_prepare_click_launch_button_button_not_found(self):
        """Return failure when Launch button not found."""
        mock_window = MagicMock()

        with patch("model.actions.osbc.find_window", return_value=mock_window):
            with patch("model.actions.osbc.find_launch_button", return_value=None):
                result = prepare_click_launch_button()

                assert result.failed is True
                assert "button not found" in result.message.lower()


class TestConfirmRuneliteWindow:
    """Tests for confirm_runelite_window function."""

    def test_confirm_runelite_window_success(self):
        """Return success when RuneLite window found."""
        mock_pywin = MagicMock()
        mock_pywin.title = "RuneLite - player123"

        with patch("model.actions.osbc.find_window", return_value=mock_pywin):
            result = confirm_runelite_window(timeout=2.0)

            assert result.success is True
            assert result.data["window_title"] == "RuneLite - player123"

    def test_confirm_runelite_window_timeout(self):
        """Return timeout when RuneLite window not found."""
        with patch("model.actions.osbc.find_window", return_value=None):
            result = confirm_runelite_window(timeout=0.1)

            assert result.timed_out is True
            assert "not detected" in result.message.lower()


class TestConfirmRuneliteLoginScreen:
    """Tests for confirm_runelite_login_screen function."""

    def test_confirm_runelite_login_screen_success(self):
        """Return success when RuneLite login screen detected."""
        from model.login.login_screen import LoginState, LoginScreenInfo

        mock_pywin = MagicMock()
        mock_pywin.title = "RuneLite - player123"

        mock_detector = MagicMock()
        mock_detector.detect_state.return_value = LoginScreenInfo(
            state=LoginState.LOGIN_SCREEN
        )

        with patch("model.actions.osbc.find_window", return_value=mock_pywin):
            with patch("utilities.window.Window"):
                with patch(
                    "model.login.login_screen.LoginScreenDetector",
                    return_value=mock_detector,
                ):
                    result = confirm_runelite_login_screen(timeout=2.0)

                    assert result.success is True
                    assert result.data["login_state"] == "LOGIN_SCREEN"

    def test_confirm_runelite_login_screen_timeout(self):
        """Return timeout when RuneLite window not found."""
        with patch("model.actions.osbc.find_window", return_value=None):
            result = confirm_runelite_login_screen(timeout=0.1)

            assert result.timed_out is True
            assert "not detected" in result.message.lower()

    def test_confirm_runelite_login_screen_not_login_state(self):
        """Timeout when RuneLite exists but not on login screen."""
        from model.login.login_screen import LoginState, LoginScreenInfo

        mock_pywin = MagicMock()
        mock_pywin.title = "RuneLite"

        mock_detector = MagicMock()
        mock_detector.detect_state.return_value = LoginScreenInfo(
            state=LoginState.LOGGED_IN  # Already logged in
        )

        with patch("model.actions.osbc.find_window", return_value=mock_pywin):
            with patch("utilities.window.Window"):
                with patch(
                    "model.login.login_screen.LoginScreenDetector",
                    return_value=mock_detector,
                ):
                    result = confirm_runelite_login_screen(timeout=0.1)

                    assert result.timed_out is True

    def test_confirm_runelite_login_screen_detection_error(self):
        """Continue trying when detection raises exception."""
        mock_pywin = MagicMock()
        mock_pywin.title = "RuneLite"

        with patch("model.actions.osbc.find_window", return_value=mock_pywin):
            with patch("utilities.window.Window", side_effect=Exception("Window error")):
                result = confirm_runelite_login_screen(timeout=0.1)

                # Should timeout, not crash
                assert result.timed_out is True
