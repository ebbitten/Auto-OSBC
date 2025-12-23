"""Login screen detection and state management.

Provides functionality to detect the current state of the game's
login screen and locate UI elements for automated login.
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from utilities.geometry import Rectangle
    from utilities.window import Window


class LoginState(Enum):
    """Possible states of the login process."""

    UNKNOWN = auto()
    LOGIN_SCREEN = auto()
    ENTERING_USERNAME = auto()
    ENTERING_PASSWORD = auto()
    CLICK_TO_PLAY = auto()
    LOBBY = auto()
    LOGGED_IN = auto()
    CONNECTION_ERROR = auto()
    INVALID_CREDENTIALS = auto()
    ACCOUNT_LOCKED = auto()
    UPDATE_REQUIRED = auto()


@dataclass
class LoginScreenInfo:
    """Information about the current login screen state.

    Attributes:
        state: The current login state
        username_field: Rectangle of the username input field (if found)
        password_field: Rectangle of the password input field (if found)
        login_button: Rectangle of the login button (if found)
        play_button: Rectangle of the "Click to Play" button (if found)
        error_message: Any error message displayed on screen
    """

    state: LoginState
    username_field: Optional["Rectangle"] = None
    password_field: Optional["Rectangle"] = None
    login_button: Optional["Rectangle"] = None
    play_button: Optional["Rectangle"] = None
    error_message: Optional[str] = None


# Path to login template images
LOGIN_IMAGES_PATH = Path(__file__).parent.parent.parent / "images" / "bot" / "login"


class LoginScreenDetector:
    """Detects the current state of the login screen.

    Uses a combination of OCR and template matching to identify:
    - Login screen elements (username/password fields, login button)
    - Error messages
    - Post-login states (click to play, lobby, logged in)
    """

    def __init__(self, window: "Window"):
        """Initialize the detector with a window.

        Args:
            window: The game window to detect login state from
        """
        self.window = window

    def detect_state(self) -> LoginScreenInfo:
        """Detect the current login screen state.

        Returns:
            LoginScreenInfo with current state and field locations
        """
        # Check if already logged in first
        if self.is_logged_in():
            return LoginScreenInfo(state=LoginState.LOGGED_IN)

        # Check if on login screen
        if self.is_on_login_screen():
            # Get field locations
            username_field = self.get_username_field_location()
            password_field = self.get_password_field_location()
            login_button = self.get_login_button_location()
            error_message = self.get_error_message()

            # Determine specific state based on error message
            if error_message:
                if "invalid" in error_message.lower():
                    return LoginScreenInfo(
                        state=LoginState.INVALID_CREDENTIALS,
                        error_message=error_message,
                    )
                elif "error" in error_message.lower() or "connect" in error_message.lower():
                    return LoginScreenInfo(
                        state=LoginState.CONNECTION_ERROR,
                        error_message=error_message,
                    )
                elif "locked" in error_message.lower() or "disabled" in error_message.lower():
                    return LoginScreenInfo(
                        state=LoginState.ACCOUNT_LOCKED,
                        error_message=error_message,
                    )

            return LoginScreenInfo(
                state=LoginState.LOGIN_SCREEN,
                username_field=username_field,
                password_field=password_field,
                login_button=login_button,
            )

        # Unknown state
        return LoginScreenInfo(state=LoginState.UNKNOWN)

    def is_on_login_screen(self) -> bool:
        """Check if currently on the login screen.

        Uses template matching for the login button, with OCR fallback.

        Returns:
            True if on login screen, False otherwise
        """
        # Try template matching first
        if self._find_login_button_template() is not None:
            return True

        # Fallback to OCR
        if self._detect_login_screen_ocr():
            return True

        return False

    def is_logged_in(self) -> bool:
        """Check if player is fully logged into the game.

        Checks for the presence of game UI elements like inventory slots.

        Returns:
            True if logged in with game UI visible, False otherwise
        """
        try:
            inventory = self.window.inventory_slots
            return inventory is not None and len(inventory) == 28
        except (AttributeError, Exception):
            return False

    def get_username_field_location(self) -> Optional["Rectangle"]:
        """Find the username text field.

        Looks for the "Username:" label via OCR and calculates
        the input field position relative to it.

        Returns:
            Rectangle of the username field, or None if not found
        """
        return self._find_username_field()

    def get_password_field_location(self) -> Optional["Rectangle"]:
        """Find the password text field.

        The password field is typically below the username field.

        Returns:
            Rectangle of the password field, or None if not found
        """
        return self._find_password_field()

    def get_login_button_location(self) -> Optional["Rectangle"]:
        """Find the login button.

        Uses template matching to find the login button.

        Returns:
            Rectangle of the login button, or None if not found
        """
        return self._find_login_button_template()

    def get_error_message(self) -> Optional[str]:
        """Extract any error message from the login screen.

        Looks for common error text like "Invalid", "Error", etc.

        Returns:
            The error message text, or None if no error visible
        """
        return self._extract_error_text()

    # Private helper methods

    def _find_login_button_template(self) -> Optional["Rectangle"]:
        """Find login button using template matching."""
        try:
            from utilities import imagesearch as imsearch

            template_path = LOGIN_IMAGES_PATH / "login_button.png"
            if not template_path.exists():
                return None

            result = imsearch.search_img_in_rect(
                str(template_path),
                self.window.rectangle(),
                confidence=0.8,
            )
            return result
        except Exception:
            return None

    def _detect_login_screen_ocr(self) -> bool:
        """Detect login screen using OCR for 'Username:' text."""
        try:
            from utilities import ocr
            from utilities.color import clr

            client_rect = self.window.rectangle()
            text = ocr.extract_text(client_rect, ocr.PLAIN_12, [clr.WHITE])
            return "username" in text.lower()
        except Exception:
            return False

    def _find_username_field(self) -> Optional["Rectangle"]:
        """Find username input field by locating 'Username:' label."""
        try:
            from utilities import ocr
            from utilities.color import clr
            from utilities.geometry import Rectangle

            client_rect = self.window.rectangle()

            # Find "Username:" label
            results = ocr.find_text(
                "Username",
                client_rect,
                ocr.PLAIN_12,
                [clr.WHITE],
            )

            if results:
                label = results[0]
                # Username field is typically centered below/right of label
                # These are approximate offsets for RuneLite
                field_left = label.left - 50
                field_top = label.top + label.height + 5
                field_width = 200
                field_height = 25
                return Rectangle(field_left, field_top, field_width, field_height)

            return None
        except Exception:
            return None

    def _find_password_field(self) -> Optional["Rectangle"]:
        """Find password input field below username field."""
        username_field = self._find_username_field()
        if username_field is None:
            return None

        try:
            from utilities.geometry import Rectangle

            # Password field is typically 30-40 pixels below username field
            return Rectangle(
                username_field.left,
                username_field.top + 35,
                username_field.width,
                username_field.height,
            )
        except Exception:
            return None

    def _extract_error_text(self) -> Optional[str]:
        """Extract error message text from login screen."""
        try:
            from utilities import ocr
            from utilities.color import clr

            client_rect = self.window.rectangle()

            # Look for error text (usually in red or orange)
            text = ocr.extract_text(client_rect, ocr.PLAIN_12, [clr.RED, clr.ORANGE])

            # Check for known error patterns
            error_patterns = [
                "invalid",
                "error",
                "locked",
                "disabled",
                "connect",
                "failed",
            ]

            text_lower = text.lower()
            for pattern in error_patterns:
                if pattern in text_lower:
                    return text.strip()

            return None
        except Exception:
            return None
