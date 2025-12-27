"""Tests for login screen detection."""

import pytest
from unittest.mock import MagicMock, patch

from model.login.login_screen import (
    LoginState,
    LoginScreenInfo,
    LoginScreenDetector,
)


class TestLoginState:
    """Tests for LoginState enum."""

    def test_login_state_values_exist(self):
        """Verify all expected login states exist."""
        assert LoginState.UNKNOWN is not None
        assert LoginState.LOGIN_SCREEN is not None
        assert LoginState.LOGGED_IN is not None
        assert LoginState.CONNECTION_ERROR is not None

    def test_login_states_are_distinct(self):
        """Each login state should have a unique value."""
        states = [
            LoginState.UNKNOWN,
            LoginState.LOGIN_SCREEN,
            LoginState.LOGGED_IN,
            LoginState.CONNECTION_ERROR,
        ]
        assert len(states) == len(set(states))


class TestLoginScreenInfo:
    """Tests for LoginScreenInfo dataclass."""

    def test_create_with_state_only(self):
        """Create LoginScreenInfo with just a state."""
        info = LoginScreenInfo(state=LoginState.LOGIN_SCREEN)
        assert info.state == LoginState.LOGIN_SCREEN
        assert info.username_field is None
        assert info.password_field is None
        assert info.login_button is None
        assert info.error_message is None

    def test_create_with_all_fields(self):
        """Create LoginScreenInfo with all fields populated."""
        from utilities.geometry import Rectangle

        username_rect = Rectangle(100, 100, 200, 25)
        password_rect = Rectangle(100, 130, 200, 25)
        login_rect = Rectangle(100, 170, 100, 30)

        info = LoginScreenInfo(
            state=LoginState.LOGIN_SCREEN,
            username_field=username_rect,
            password_field=password_rect,
            login_button=login_rect,
        )

        assert info.state == LoginState.LOGIN_SCREEN
        assert info.username_field == username_rect
        assert info.password_field == password_rect
        assert info.login_button == login_rect

    def test_create_with_error_message(self):
        """Create LoginScreenInfo with error message."""
        info = LoginScreenInfo(
            state=LoginState.CONNECTION_ERROR,
            error_message="Connection error",
        )
        assert info.state == LoginState.CONNECTION_ERROR
        assert info.error_message == "Connection error"


class TestLoginScreenDetector:
    """Tests for LoginScreenDetector."""

    @pytest.fixture
    def mock_window(self):
        """Create a mock window object."""
        window = MagicMock()
        window.rectangle.return_value = MagicMock(left=0, top=0, width=800, height=600)
        window.inventory_slots = None
        # Make initialize() raise to simulate not being logged in
        window.initialize.side_effect = Exception("Not logged in")
        return window

    def test_init_with_window(self, mock_window):
        """Detector initializes with a window."""
        detector = LoginScreenDetector(mock_window)
        assert detector.window == mock_window

    def test_is_on_login_screen_true_when_login_button_found(self, mock_window):
        """is_on_login_screen returns True when login button template found."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_find_login_button_template") as mock_find:
            mock_find.return_value = MagicMock()  # Found something
            assert detector.is_on_login_screen() is True

    def test_is_on_login_screen_true_when_username_text_found(self, mock_window):
        """is_on_login_screen returns True when 'Username:' OCR text found."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_find_login_button_template") as mock_template:
            mock_template.return_value = None  # Template not found
            with patch.object(detector, "_detect_login_screen_ocr") as mock_ocr:
                mock_ocr.return_value = True
                assert detector.is_on_login_screen() is True

    def test_is_on_login_screen_false_when_nothing_found(self, mock_window):
        """is_on_login_screen returns False when no login indicators found."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_find_login_button_template") as mock_template:
            mock_template.return_value = None
            with patch.object(detector, "_detect_login_screen_ocr") as mock_ocr:
                mock_ocr.return_value = False
                assert detector.is_on_login_screen() is False

    def test_is_logged_in_true_when_inventory_present(self, mock_window):
        """is_logged_in returns True when inventory slots are present."""
        mock_window.inventory_slots = [MagicMock()] * 28  # 28 inventory slots
        detector = LoginScreenDetector(mock_window)

        assert detector.is_logged_in() is True

    def test_is_logged_in_false_when_no_inventory(self, mock_window):
        """is_logged_in returns False when no inventory slots and no minimap orbs."""
        mock_window.inventory_slots = None
        detector = LoginScreenDetector(mock_window)

        # Mock _has_minimap_orbs to return False (not in game)
        with patch.object(detector, "_has_minimap_orbs", return_value=False):
            assert detector.is_logged_in() is False

    def test_is_logged_in_false_when_inventory_incomplete(self, mock_window):
        """is_logged_in returns False when inventory has wrong slot count and no minimap orbs."""
        mock_window.inventory_slots = [MagicMock()] * 10  # Only 10 slots
        detector = LoginScreenDetector(mock_window)

        # Mock _has_minimap_orbs to return False (not in game)
        with patch.object(detector, "_has_minimap_orbs", return_value=False):
            assert detector.is_logged_in() is False

    def test_detect_state_returns_logged_in_when_in_game(self, mock_window):
        """detect_state returns LOGGED_IN when game UI is visible."""
        mock_window.inventory_slots = [MagicMock()] * 28
        detector = LoginScreenDetector(mock_window)

        info = detector.detect_state()
        assert info.state == LoginState.LOGGED_IN

    def test_detect_state_returns_login_screen_when_detected(self, mock_window):
        """detect_state returns LOGIN_SCREEN when on login screen."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_check_welcome_screen", return_value=None):
            with patch.object(detector, "_find_login_button_template") as mock_find:
                mock_find.return_value = MagicMock()
                with patch.object(detector, "_is_login_screen", return_value=True):
                    info = detector.detect_state()
                    assert info.state == LoginState.LOGIN_SCREEN

    def test_detect_state_returns_unknown_when_nothing_detected(self, mock_window):
        """detect_state returns UNKNOWN when state cannot be determined."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "is_logged_in", return_value=False):
            with patch.object(detector, "is_on_login_screen", return_value=False):
                info = detector.detect_state()
                assert info.state == LoginState.UNKNOWN

    def test_get_username_field_location_returns_rectangle(self, mock_window):
        """get_username_field_location returns a Rectangle when found."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_find_username_field") as mock_find:
            from utilities.geometry import Rectangle

            expected = Rectangle(100, 100, 200, 25)
            mock_find.return_value = expected

            result = detector.get_username_field_location()
            assert result == expected

    def test_get_username_field_location_returns_none_when_not_found(self, mock_window):
        """get_username_field_location returns None when field not found."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_find_username_field") as mock_find:
            mock_find.return_value = None
            result = detector.get_username_field_location()
            assert result is None

    def test_get_login_button_location_returns_rectangle(self, mock_window):
        """get_login_button_location returns Rectangle when found."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_find_login_button_template") as mock_find:
            from utilities.geometry import Rectangle

            expected = Rectangle(350, 400, 100, 30)
            mock_find.return_value = expected

            result = detector.get_login_button_location()
            assert result == expected

    def test_get_error_message_extracts_invalid_credentials(self, mock_window):
        """get_error_message extracts 'Invalid' error message."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_extract_error_text") as mock_extract:
            mock_extract.return_value = "Invalid username or password"
            result = detector.get_error_message()
            assert "Invalid" in result

    def test_get_error_message_returns_none_when_no_error(self, mock_window):
        """get_error_message returns None when no error is visible."""
        detector = LoginScreenDetector(mock_window)

        with patch.object(detector, "_extract_error_text") as mock_extract:
            mock_extract.return_value = None
            result = detector.get_error_message()
            assert result is None
