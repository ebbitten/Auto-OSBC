"""Unit tests for the minimal CLI."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cli import create_parser, main


class TestCreateParser:
    """Test CLI parser creation."""

    def test_parser_has_all_commands(self):
        """Test that parser has exactly 4 commands."""
        parser = create_parser()

        subparsers_action = None
        for action in parser._actions:
            if hasattr(action, "_parser_class"):
                subparsers_action = action
                break

        assert subparsers_action is not None
        choices = list(subparsers_action.choices.keys())

        # Only 4 commands
        assert len(choices) == 4
        assert "start" in choices
        assert "gui" in choices
        assert "login" in choices
        assert "status" in choices

    def test_parser_prog_name(self):
        """Test that parser has correct program name."""
        parser = create_parser()
        assert parser.prog == "osbc"


class TestStartCommand:
    """Test the 'start' command."""

    def test_start_default_args(self):
        """Test start with default arguments."""
        parser = create_parser()
        args = parser.parse_args(["start"])

        assert args.command == "start"
        assert args.game == "OSRS"
        assert args.timeout == 120.0
        assert args.no_launch is False
        assert args.headless is False
        assert args.force_gui is False
        assert args.force is False

    def test_start_custom_game(self):
        """Test start with custom game."""
        parser = create_parser()
        args = parser.parse_args(["start", "--game", "Alora"])
        assert args.game == "Alora"

    def test_start_headless(self):
        """Test start with headless flag."""
        parser = create_parser()
        args = parser.parse_args(["start", "--headless"])
        assert args.headless is True

    def test_start_no_launch(self):
        """Test start with no-launch flag."""
        parser = create_parser()
        args = parser.parse_args(["start", "--no-launch"])
        assert args.no_launch is True


class TestGuiCommand:
    """Test the 'gui' command."""

    def test_gui_no_args(self):
        """Test gui command has no required args."""
        parser = create_parser()
        args = parser.parse_args(["gui"])
        assert args.command == "gui"


class TestLoginCommand:
    """Test the 'login' command."""

    def test_login_default_args(self):
        """Test login with default arguments."""
        parser = create_parser()
        args = parser.parse_args(["login"])

        assert args.command == "login"
        assert args.window == "RuneLite"
        assert args.max_attempts == 3

    def test_login_custom_window(self):
        """Test login with custom window."""
        parser = create_parser()
        args = parser.parse_args(["login", "--window", "Custom"])
        assert args.window == "Custom"

    def test_login_max_attempts(self):
        """Test login with custom max attempts."""
        parser = create_parser()
        args = parser.parse_args(["login", "--max-attempts", "5"])
        assert args.max_attempts == 5


class TestStatusCommand:
    """Test the 'status' command."""

    def test_status_default_args(self):
        """Test status with default arguments."""
        parser = create_parser()
        args = parser.parse_args(["status"])

        assert args.command == "status"
        assert args.verbose is False

    def test_status_verbose(self):
        """Test status with verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["status", "-v"])
        assert args.verbose is True


class TestCommandDispatch:
    """Test that commands dispatch to correct handlers."""

    @patch("cli.cmd_start")
    def test_start_dispatch(self, mock_cmd):
        """Test start dispatches correctly."""
        mock_cmd.return_value = 0
        parser = create_parser()
        args = parser.parse_args(["start"])

        result = args.func(args)

        mock_cmd.assert_called_once_with(args)
        assert result == 0

    @patch("cli.cmd_gui")
    def test_gui_dispatch(self, mock_cmd):
        """Test gui dispatches correctly."""
        mock_cmd.return_value = 0
        parser = create_parser()
        args = parser.parse_args(["gui"])

        result = args.func(args)

        mock_cmd.assert_called_once_with(args)
        assert result == 0

    @patch("cli.cmd_login")
    def test_login_dispatch(self, mock_cmd):
        """Test login dispatches correctly."""
        mock_cmd.return_value = 0
        parser = create_parser()
        args = parser.parse_args(["login"])

        result = args.func(args)

        mock_cmd.assert_called_once_with(args)
        assert result == 0

    @patch("cli.cmd_status")
    def test_status_dispatch(self, mock_cmd):
        """Test status dispatches correctly."""
        mock_cmd.return_value = 0
        parser = create_parser()
        args = parser.parse_args(["status"])

        result = args.func(args)

        mock_cmd.assert_called_once_with(args)
        assert result == 0


class TestCmdHandlers:
    """Test command handler functions."""

    def test_cmd_start_headless_success(self):
        """Test start --headless with successful launch."""
        from model.actions.base import ActionOutcome

        mock_orchestration = MagicMock()
        mock_result = ActionOutcome.ok("Success", runelite_title="RuneLite")
        mock_orchestration.auto_launch_runelite.return_value = mock_result

        with patch.dict("sys.modules", {"model.actions": MagicMock(orchestration=mock_orchestration)}):
            parser = create_parser()
            args = parser.parse_args(["start", "--headless"])

            from cli import cmd_start
            result = cmd_start(args)

            assert result == 0
            mock_orchestration.auto_launch_runelite.assert_called_once()

    def test_cmd_start_no_launch(self):
        """Test start --no-launch skips orchestration."""
        with patch("cli.cmd_gui") as mock_gui:
            mock_gui.return_value = 0
            parser = create_parser()
            args = parser.parse_args(["start", "--no-launch"])

            from cli import cmd_start
            result = cmd_start(args)

            mock_gui.assert_called_once_with(args)
            assert result == 0

    def test_cmd_login_success(self):
        """Test login with successful result."""
        from model.actions.base import ActionOutcome

        mock_login = MagicMock()
        mock_result = ActionOutcome.ok("Login successful")
        mock_login.perform_login.return_value = mock_result

        with patch.dict("sys.modules", {"model.actions": MagicMock(login=mock_login)}):
            parser = create_parser()
            args = parser.parse_args(["login"])

            from cli import cmd_login
            result = cmd_login(args)

            assert result == 0
            mock_login.perform_login.assert_called_once()

    def test_cmd_login_failure(self):
        """Test login with failed result."""
        from model.actions.base import ActionOutcome

        mock_login = MagicMock()
        mock_result = ActionOutcome.fail("Login failed")
        mock_login.perform_login.return_value = mock_result

        with patch.dict("sys.modules", {"model.actions": MagicMock(login=mock_login)}):
            parser = create_parser()
            args = parser.parse_args(["login"])

            from cli import cmd_login
            result = cmd_login(args)

            assert result == 1

    def test_cmd_status(self):
        """Test status command."""
        from model.actions.base import ActionOutcome

        mock_osbc = MagicMock()
        mock_result = ActionOutcome.ok(
            "Status",
            osbc_running=True,
            runelite_running=True,
            osbc_title="OS Bot",
            runelite_title="RuneLite",
        )
        mock_osbc.check_windows_status.return_value = mock_result

        with patch.dict("sys.modules", {"model.actions": MagicMock(osbc=mock_osbc)}):
            parser = create_parser()
            args = parser.parse_args(["status"])

            from cli import cmd_status
            result = cmd_status(args)

            assert result == 0
            mock_osbc.check_windows_status.assert_called_once()


class TestMain:
    """Test main entry point."""

    @patch("cli.create_parser")
    def test_main_calls_func(self, mock_create_parser):
        """Test main calls the command function."""
        mock_args = MagicMock()
        mock_args.func.return_value = 0
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        result = main()

        assert result == 0
        mock_args.func.assert_called_once_with(mock_args)

    @patch("cli.create_parser")
    def test_main_handles_exception(self, mock_create_parser):
        """Test main handles exceptions gracefully."""
        mock_args = MagicMock()
        mock_args.func.side_effect = Exception("Test error")
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        result = main()

        assert result == 1
