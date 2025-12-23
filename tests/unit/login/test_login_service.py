"""Tests for login service and credentials."""

import pytest
from unittest.mock import MagicMock, patch
import os

from model.login.login_service import LoginCredentials, LoginService
from model.login.login_screen import LoginState, LoginScreenInfo
from model.actions.base import ActionOutcome
from model.actions.intents import (
    ClickIntent,
    CompositeIntent,
    KeyPressIntent,
    TypeIntent,
)
from model.actions.executor import MockExecutor


class TestLoginCredentials:
    """Tests for LoginCredentials class."""

    def test_loads_username_from_env(self, monkeypatch):
        """Load username from OSBC_USERNAME environment variable."""
        monkeypatch.setenv("OSBC_USERNAME", "test_user")
        monkeypatch.setenv("OSBC_PASSWORD", "test_pass")

        creds = LoginCredentials()
        assert creds.username == "test_user"

    def test_loads_password_from_env(self, monkeypatch):
        """Load password from OSBC_PASSWORD environment variable."""
        monkeypatch.setenv("OSBC_USERNAME", "test_user")
        monkeypatch.setenv("OSBC_PASSWORD", "secret123")

        creds = LoginCredentials()
        assert creds.password == "secret123"

    def test_override_username_takes_precedence(self, monkeypatch):
        """Explicit username overrides environment variable."""
        monkeypatch.setenv("OSBC_USERNAME", "env_user")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        creds = LoginCredentials(username="override_user")
        assert creds.username == "override_user"

    def test_override_password_takes_precedence(self, monkeypatch):
        """Explicit password overrides environment variable."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "env_pass")

        creds = LoginCredentials(password="override_pass")
        assert creds.password == "override_pass"

    def test_is_configured_true_when_both_present(self, monkeypatch):
        """is_configured returns True when both credentials are set."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        creds = LoginCredentials()
        assert creds.is_configured() is True

    def test_is_configured_false_when_username_missing(self, monkeypatch):
        """is_configured returns False when username is missing."""
        monkeypatch.setenv("OSBC_USERNAME", "")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        creds = LoginCredentials(username="", password="pass")
        assert creds.is_configured() is False

    def test_is_configured_false_when_password_missing(self, monkeypatch):
        """is_configured returns False when password is missing."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "")

        creds = LoginCredentials(username="user", password="")
        assert creds.is_configured() is False

    def test_is_configured_false_when_username_empty(self, monkeypatch):
        """is_configured returns False when username is empty string."""
        monkeypatch.setenv("OSBC_USERNAME", "")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        creds = LoginCredentials()
        assert creds.is_configured() is False

    def test_is_configured_false_when_password_empty(self, monkeypatch):
        """is_configured returns False when password is empty string."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "")

        creds = LoginCredentials()
        assert creds.is_configured() is False

    def test_defaults_to_empty_when_explicit_empty(self, monkeypatch):
        """Credentials can be explicitly set to empty strings."""
        creds = LoginCredentials(username="", password="")
        assert creds.username == ""
        assert creds.password == ""
        assert creds.is_configured() is False


class TestLoginService:
    """Tests for LoginService class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.win = MagicMock()
        bot.win.rectangle.return_value = MagicMock(left=0, top=0, width=800, height=600)
        bot.win.inventory_slots = None
        bot.mouse = MagicMock()
        bot.log_msg = MagicMock()
        return bot

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor."""
        return MockExecutor()

    def test_init_with_bot(self, mock_bot):
        """LoginService initializes with a bot."""
        service = LoginService(mock_bot)
        assert service.bot == mock_bot

    def test_login_fails_when_credentials_not_configured(self, mock_bot, monkeypatch):
        """login() fails immediately when credentials not configured."""
        # Force empty credentials by passing explicit empty strings
        service = LoginService(mock_bot)
        result = service.login(username="", password="")

        assert result.failed is True
        assert "credentials" in result.message.lower()

    def test_login_returns_success_when_already_logged_in(self, mock_bot, monkeypatch):
        """login() returns success immediately if already logged in."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")
        mock_bot.win.inventory_slots = [MagicMock()] * 28  # Simulate logged in

        service = LoginService(mock_bot)
        result = service.login()

        assert result.success is True
        assert "already" in result.message.lower()

    def test_login_uses_env_credentials(self, mock_bot, monkeypatch):
        """login() uses credentials from environment variables."""
        monkeypatch.setenv("OSBC_USERNAME", "env_user")
        monkeypatch.setenv("OSBC_PASSWORD", "env_pass")

        service = LoginService(mock_bot)
        creds = service._get_credentials(None, None)

        assert creds.username == "env_user"
        assert creds.password == "env_pass"

    def test_login_uses_override_credentials(self, mock_bot, monkeypatch):
        """login() uses override credentials when provided."""
        monkeypatch.setenv("OSBC_USERNAME", "env_user")
        monkeypatch.setenv("OSBC_PASSWORD", "env_pass")

        service = LoginService(mock_bot)
        creds = service._get_credentials("override_user", "override_pass")

        assert creds.username == "override_user"
        assert creds.password == "override_pass"

    def test_login_builds_correct_intent_sequence(self, mock_bot, monkeypatch):
        """login() builds a CompositeIntent with correct sequence."""
        monkeypatch.setenv("OSBC_USERNAME", "testuser")
        monkeypatch.setenv("OSBC_PASSWORD", "testpass")

        service = LoginService(mock_bot)

        # Mock the detector to return login screen state
        with patch.object(service, "detector") as mock_detector:
            from utilities.geometry import Rectangle

            mock_detector.is_logged_in.return_value = False
            mock_detector.is_on_login_screen.return_value = True
            mock_detector.get_username_field_location.return_value = Rectangle(
                100, 100, 200, 25
            )
            mock_detector.get_password_field_location.return_value = Rectangle(
                100, 130, 200, 25
            )
            mock_detector.get_login_button_location.return_value = Rectangle(
                100, 170, 100, 30
            )

            # Build the intent sequence
            sequence = service._build_login_sequence("testuser", "testpass")

            assert isinstance(sequence, CompositeIntent)

            # Check the sequence contains expected intent types
            intent_types = [type(i).__name__ for i in sequence.intents]

            assert "ClickIntent" in intent_types  # Click username field
            assert "TypeIntent" in intent_types  # Type username
            assert "KeyPressIntent" in intent_types  # Tab key
            # Should have TypeIntent for password too

    def test_login_password_intent_is_masked(self, mock_bot, monkeypatch):
        """Password TypeIntent has mask_in_logs=True."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "secret")

        service = LoginService(mock_bot)

        with patch.object(service, "detector") as mock_detector:
            from utilities.geometry import Rectangle

            mock_detector.is_logged_in.return_value = False
            mock_detector.is_on_login_screen.return_value = True
            mock_detector.get_username_field_location.return_value = Rectangle(
                100, 100, 200, 25
            )
            mock_detector.get_password_field_location.return_value = Rectangle(
                100, 130, 200, 25
            )
            mock_detector.get_login_button_location.return_value = Rectangle(
                100, 170, 100, 30
            )

            sequence = service._build_login_sequence("user", "secret")

            # Find the password TypeIntent
            type_intents = [i for i in sequence.intents if isinstance(i, TypeIntent)]
            password_intent = [i for i in type_intents if i.text == "secret"][0]

            assert password_intent.mask_in_logs is True

    def test_login_username_intent_not_masked(self, mock_bot, monkeypatch):
        """Username TypeIntent does not have mask_in_logs=True."""
        monkeypatch.setenv("OSBC_USERNAME", "myuser")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        service = LoginService(mock_bot)

        with patch.object(service, "detector") as mock_detector:
            from utilities.geometry import Rectangle

            mock_detector.is_logged_in.return_value = False
            mock_detector.is_on_login_screen.return_value = True
            mock_detector.get_username_field_location.return_value = Rectangle(
                100, 100, 200, 25
            )
            mock_detector.get_password_field_location.return_value = Rectangle(
                100, 130, 200, 25
            )
            mock_detector.get_login_button_location.return_value = Rectangle(
                100, 170, 100, 30
            )

            sequence = service._build_login_sequence("myuser", "pass")

            # Find the username TypeIntent
            type_intents = [i for i in sequence.intents if isinstance(i, TypeIntent)]
            username_intent = [i for i in type_intents if i.text == "myuser"][0]

            assert username_intent.mask_in_logs is False

    def test_login_retries_on_connection_error(self, mock_bot, monkeypatch):
        """login() retries when connection error occurs."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        service = LoginService(mock_bot)
        attempt_count = 0

        def mock_execute(sequence):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                return ActionOutcome.fail("Connection error")
            return ActionOutcome.ok("Login successful")

        with patch.object(service, "detector") as mock_detector:
            mock_detector.is_logged_in.return_value = False
            mock_detector.is_on_login_screen.return_value = True
            mock_detector.get_error_message.return_value = "Error connecting"

            with patch.object(service, "_execute_login_sequence", side_effect=mock_execute):
                with patch.object(service, "_build_login_sequence") as mock_build:
                    mock_build.return_value = CompositeIntent(intents=[])
                    result = service.login(max_attempts=3)

        assert attempt_count == 3

    def test_login_no_retry_on_invalid_credentials(self, mock_bot, monkeypatch):
        """login() does not retry when credentials are invalid."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "wrong")

        service = LoginService(mock_bot)
        attempt_count = 0

        def mock_execute(sequence):
            nonlocal attempt_count
            attempt_count += 1
            return ActionOutcome.fail("Invalid credentials")

        with patch.object(service, "detector") as mock_detector:
            mock_detector.is_logged_in.return_value = False
            mock_detector.is_on_login_screen.return_value = True
            mock_detector.get_error_message.return_value = "Invalid username or password"

            with patch.object(service, "_execute_login_sequence", side_effect=mock_execute):
                with patch.object(service, "_build_login_sequence") as mock_build:
                    mock_build.return_value = CompositeIntent(intents=[])
                    result = service.login(max_attempts=3)

        # Should only try once when credentials are invalid
        assert attempt_count == 1
        assert result.failed is True
        assert "invalid" in result.message.lower()

    def test_login_fails_when_fields_not_found(self, mock_bot, monkeypatch):
        """login() fails when login screen fields cannot be found."""
        monkeypatch.setenv("OSBC_USERNAME", "user")
        monkeypatch.setenv("OSBC_PASSWORD", "pass")

        service = LoginService(mock_bot)

        with patch.object(service, "detector") as mock_detector:
            mock_detector.is_logged_in.return_value = False
            mock_detector.is_on_login_screen.return_value = True
            mock_detector.get_username_field_location.return_value = None  # Not found
            mock_detector.get_password_field_location.return_value = None
            mock_detector.get_login_button_location.return_value = None

            result = service.login()

        assert result.failed is True
        assert "field" in result.message.lower() or "button" in result.message.lower()
