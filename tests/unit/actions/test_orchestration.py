"""Tests for orchestration module - multi-step workflows."""

import pytest
from unittest.mock import MagicMock, patch, call

from model.actions.orchestration import (
    auto_launch_runelite,
    shutdown_all,
)
from model.actions.base import ActionOutcome
from model.actions.intents import LaunchIntent, ClickIntent


class TestAutoLaunchRunelite:
    """Tests for auto_launch_runelite orchestration function."""

    def test_skip_if_runelite_already_running(self):
        """Skip launch if RuneLite is already running."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=True,
            osbc_title="OS Bot COLOR",
            runelite_title="RuneLite - player123",
        )

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            result = auto_launch_runelite(skip_if_running=True)

            assert result.success is True
            assert result.data.get("skipped") is True
            assert "already running" in result.message.lower()

    def test_no_skip_when_runelite_running(self):
        """Continue with launch even if RuneLite running when skip_if_running=False."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=True,
            osbc_title="OS Bot COLOR",
            runelite_title="RuneLite - player123",
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="OSRS",
        )

        mock_launch_btn = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(420, 450)),
            button_point=(420, 450),
        )

        mock_confirm = ActionOutcome.ok(
            "RuneLite detected",
            window_title="RuneLite - player123",
            elapsed_seconds=5.0,
        )

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select):
                    with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                        with patch("model.actions.orchestration.osbc.confirm_runelite_window", return_value=mock_confirm):
                            with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                                result = auto_launch_runelite(skip_if_running=False)

                                assert result.success is True
                                assert result.data.get("skipped") is None

    def test_launch_osbc_if_not_running(self):
        """Launch OSBC when it's not running."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=False,
            runelite_running=False,
            osbc_title=None,
            runelite_title=None,
        )

        mock_launch_osbc = ActionOutcome.ok(
            "Ready to launch",
            intent=LaunchIntent(command=["osbc", "gui"], expected_window="OS Bot"),
            executable="osbc.exe",
        )

        mock_wait = ActionOutcome.ok(
            "Window found",
            window_title="OS Bot COLOR",
            elapsed_seconds=2.0,
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="OSRS",
        )

        mock_launch_btn = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(420, 450)),
            button_point=(420, 450),
        )

        mock_confirm = ActionOutcome.ok(
            "RuneLite detected",
            window_title="RuneLite - player123",
            elapsed_seconds=10.0,
        )

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.window.prepare_launch_osbc", return_value=mock_launch_osbc):
                with patch("model.actions.orchestration.window.wait_for_window", return_value=mock_wait):
                    with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                        with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select):
                            with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                                with patch("model.actions.orchestration.osbc.confirm_runelite_window", return_value=mock_confirm):
                                    with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                                        result = auto_launch_runelite()

                                        assert result.success is True
                                        assert "OSBC launched" in str(result.data.get("steps", []))

    def test_fail_if_osbc_launch_fails(self):
        """Return failure if OSBC cannot be launched."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=False,
            runelite_running=False,
            osbc_title=None,
            runelite_title=None,
        )

        mock_launch_osbc = ActionOutcome.fail(
            "Could not find osbc executable",
            searched_path="/usr/bin",
        )

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.window.prepare_launch_osbc", return_value=mock_launch_osbc):
                result = auto_launch_runelite()

                assert result.failed is True
                assert "osbc" in result.message.lower()

    def test_fail_if_dropdown_not_found(self):
        """Return failure if game dropdown cannot be found."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=False,
            osbc_title="OS Bot COLOR",
            runelite_title=None,
        )

        mock_dropdown = ActionOutcome.fail("OSBC window not found")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                result = auto_launch_runelite()

                assert result.failed is True
                assert "dropdown" in result.message.lower()

    def test_fail_if_launch_button_not_found(self):
        """Return failure if Launch button cannot be found."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=False,
            osbc_title="OS Bot COLOR",
            runelite_title=None,
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="OSRS",
        )

        mock_launch_btn = ActionOutcome.fail("Launch button not found")

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select):
                    with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                        with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                            result = auto_launch_runelite()

                            assert result.failed is True
                            assert "launch button" in result.message.lower()

    def test_timeout_if_runelite_not_detected(self):
        """Return timeout if RuneLite window doesn't appear."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=False,
            osbc_title="OS Bot COLOR",
            runelite_title=None,
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="OSRS",
        )

        mock_launch_btn = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(420, 450)),
            button_point=(420, 450),
        )

        mock_confirm = ActionOutcome.timeout(
            "RuneLite not detected within 5s",
            timeout_seconds=5.0,
        )

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select):
                    with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                        with patch("model.actions.orchestration.osbc.confirm_runelite_window", return_value=mock_confirm):
                            with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                                result = auto_launch_runelite(timeout=5.0)

                                assert result.timed_out is True
                                assert "runelite" in result.message.lower()

    def test_login_flag_sets_pending(self):
        """When login=True, result indicates login is pending."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=False,
            osbc_title="OS Bot COLOR",
            runelite_title=None,
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="OSRS",
        )

        mock_launch_btn = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(420, 450)),
            button_point=(420, 450),
        )

        mock_confirm = ActionOutcome.ok(
            "RuneLite detected",
            window_title="RuneLite - player123",
            elapsed_seconds=10.0,
        )

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select):
                    with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                        with patch("model.actions.orchestration.osbc.confirm_runelite_window", return_value=mock_confirm):
                            with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                                result = auto_launch_runelite(login=True)

                                assert result.success is True
                                assert result.data.get("login_pending") is True

    def test_custom_game_selection(self):
        """Support selecting different games."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=False,
            osbc_title="OS Bot COLOR",
            runelite_title=None,
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="Alora",
        )

        mock_launch_btn = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(420, 450)),
            button_point=(420, 450),
        )

        mock_confirm = ActionOutcome.ok(
            "RuneLite detected",
            window_title="RuneLite - player123",
            elapsed_seconds=10.0,
        )

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select) as mock_select_fn:
                    with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                        with patch("model.actions.orchestration.osbc.confirm_runelite_window", return_value=mock_confirm):
                            with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                                result = auto_launch_runelite(game="Alora")

                                mock_select_fn.assert_called_once_with("Alora")
                                assert result.success is True

    def test_steps_tracking(self):
        """Track all steps taken during workflow."""
        mock_status = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=False,
            osbc_title="OS Bot COLOR",
            runelite_title=None,
        )

        mock_dropdown = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 100)),
            dropdown_point=(100, 100),
        )

        mock_select = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(100, 130)),
            game_name="OSRS",
        )

        mock_launch_btn = ActionOutcome.ok(
            "Ready",
            intent=ClickIntent(point=(420, 450)),
            button_point=(420, 450),
        )

        mock_confirm = ActionOutcome.ok(
            "RuneLite detected",
            window_title="RuneLite - player123",
            elapsed_seconds=10.0,
        )

        mock_executor = MagicMock()
        mock_executor.execute.return_value = ActionOutcome.ok("Executed")

        with patch("model.actions.orchestration.osbc.check_windows_status", return_value=mock_status):
            with patch("model.actions.orchestration.osbc.prepare_click_game_dropdown", return_value=mock_dropdown):
                with patch("model.actions.orchestration.osbc.prepare_select_game", return_value=mock_select):
                    with patch("model.actions.orchestration.osbc.prepare_click_launch_button", return_value=mock_launch_btn):
                        with patch("model.actions.orchestration.osbc.confirm_runelite_window", return_value=mock_confirm):
                            with patch("model.actions.orchestration.Executor", return_value=mock_executor):
                                result = auto_launch_runelite()

                                steps = result.data.get("steps", [])
                                assert len(steps) > 0
                                assert any("Status" in s for s in steps)
                                assert any("RuneLite" in s for s in steps)


class TestShutdownAll:
    """Tests for shutdown_all function."""

    def test_close_both_windows(self):
        """Close both RuneLite and OSBC windows."""
        mock_runelite = MagicMock()
        mock_osbc = MagicMock()

        def find_window_mock(title):
            if "RuneLite" in title:
                return mock_runelite
            if "OS Bot" in title:
                return mock_osbc
            return None

        with patch("model.actions.orchestration.window.find_window", side_effect=find_window_mock):
            result = shutdown_all()

            assert result.success is True
            assert "RuneLite" in result.data["closed"]
            assert "OSBC" in result.data["closed"]
            mock_runelite.close.assert_called_once()
            mock_osbc.close.assert_called_once()

    def test_close_only_runelite(self):
        """Close only RuneLite when close_osbc=False."""
        mock_runelite = MagicMock()
        mock_osbc = MagicMock()

        def find_window_mock(title):
            if "RuneLite" in title:
                return mock_runelite
            if "OS Bot" in title:
                return mock_osbc
            return None

        with patch("model.actions.orchestration.window.find_window", side_effect=find_window_mock):
            result = shutdown_all(close_osbc=False)

            assert result.success is True
            assert "RuneLite" in result.data["closed"]
            assert "OSBC" not in result.data["closed"]
            mock_runelite.close.assert_called_once()
            mock_osbc.close.assert_not_called()

    def test_no_windows_to_close(self):
        """Return success when no windows are running."""
        with patch("model.actions.orchestration.window.find_window", return_value=None):
            result = shutdown_all()

            assert result.success is True
            assert "no windows" in result.message.lower()

    def test_handle_close_error(self):
        """Return failure if close raises exception."""
        mock_runelite = MagicMock()
        mock_runelite.close.side_effect = Exception("Access denied")

        with patch("model.actions.orchestration.window.find_window", return_value=mock_runelite):
            result = shutdown_all()

            assert result.failed is True
            assert "failed to close" in result.message.lower()
