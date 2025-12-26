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
    WELCOME_SCREEN = auto()  # Initial screen with "New User" / "Existing User" buttons
    LOGIN_SCREEN = auto()  # Username/password entry screen
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
        existing_user_button: Rectangle of the "Existing User" button (if found)
        error_message: Any error message displayed on screen
    """

    state: LoginState
    username_field: Optional["Rectangle"] = None
    password_field: Optional["Rectangle"] = None
    login_button: Optional["Rectangle"] = None
    play_button: Optional["Rectangle"] = None
    existing_user_button: Optional["Rectangle"] = None
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

        # Check for "Click to Play" button (post-login state)
        play_button = self.get_click_to_play_button_location()
        if play_button:
            return LoginScreenInfo(
                state=LoginState.CLICK_TO_PLAY,
                play_button=play_button,
            )

        # Use UNIQUE identifiers to distinguish screens:
        # - "New User" + "Existing User" buttons side by side = WELCOME_SCREEN
        # - "Try again" button = INVALID_CREDENTIALS
        # - "Login" button = LOGIN_SCREEN
        #
        # IMPORTANT: Check WELCOME first because it uses structural validation
        # (both buttons at same Y position). Individual templates can have false
        # positives on brown scroll textures.

        # Check for WELCOME_SCREEN first using structural validation (most reliable)
        if self._is_welcome_screen():
            existing_user = self.get_existing_user_button_location()
            return LoginScreenInfo(
                state=LoginState.WELCOME_SCREEN,
                existing_user_button=existing_user,
            )

        # Check for LOGIN_SCREEN first (has Login button)
        # Must check before INVALID_CREDENTIALS because "Try again" template
        # can match brown scroll texture on login screen
        login_button = self.get_login_button_location()
        if login_button:
            username_field = self.get_username_field_location()
            password_field = self.get_password_field_location()
            error_message = self.get_error_message()

            return LoginScreenInfo(
                state=LoginState.LOGIN_SCREEN,
                username_field=username_field,
                password_field=password_field,
                login_button=login_button,
                error_message=error_message,
            )

        # Check for INVALID_CREDENTIALS screen (has "Try again" button but NO Login button)
        # Only check after ruling out LOGIN screen
        try_again_button = self.get_try_again_button_location()
        if try_again_button:
            return LoginScreenInfo(
                state=LoginState.INVALID_CREDENTIALS,
                error_message="Incorrect username or password",
            )

        # Unknown state
        return LoginScreenInfo(state=LoginState.UNKNOWN)

    def is_on_login_screen(self) -> bool:
        """Check if currently on the login screen.

        Uses template matching for login elements, with OCR fallback.

        Returns:
            True if on login screen, False otherwise
        """
        # Try template matching for login button (username/password screen)
        if self._find_login_button_template() is not None:
            return True

        # Try template matching for welcome screen (initial screen)
        if self._find_welcome_screen_template() is not None:
            return True

        # Fallback to OCR
        if self._detect_login_screen_ocr():
            return True

        return False

    def is_logged_in(self) -> bool:
        """Check if player is fully logged into the game.

        Checks for the presence of game UI elements. Tries multiple methods:
        1. Check if window can be initialized (finds minimap, chat, control panel)
        2. Check for minimap orbs in expected location
        3. Check for inventory slots

        Returns:
            True if logged in with game UI visible, False otherwise
        """
        try:
            # Try to initialize window - this finds game UI elements
            # If it succeeds, we're logged in
            self.window.initialize()
            return True
        except Exception:
            pass

        # Fallback: check for minimap orbs in the top-right corner
        # These only appear when logged in
        try:
            if self._has_minimap_orbs():
                return True
        except Exception:
            pass

        # Fallback: check if inventory_slots was previously populated
        try:
            inventory = self.window.inventory_slots
            if inventory is not None and len(inventory) == 28:
                return True
        except (AttributeError, Exception):
            pass

        return False

    def _has_minimap_orbs(self) -> bool:
        """Check if minimap orbs are visible (indicates logged-in state).

        The orbs (HP, prayer, run energy, special) appear in the top-right
        corner only when logged in.

        Returns:
            True if orbs are detected, False otherwise
        """
        try:
            import mss
            import numpy as np

            win_rect = self.window.rectangle()

            # Orbs are in the top-right area, roughly 150x150 from corner
            orb_area = {
                'left': win_rect.left + win_rect.width - 180,
                'top': win_rect.top + 30,  # Skip title bar
                'width': 150,
                'height': 150,
            }

            with mss.mss() as sct:
                img = np.array(sct.grab(orb_area))

                # The orbs have distinctive orange/yellow colors (HP, run, spec)
                # Check for presence of orange-ish pixels (BGR format)
                # Orange is roughly B=0-100, G=100-200, R=200-255
                orange_mask = (
                    (img[:, :, 0] < 100) &  # Low blue
                    (img[:, :, 1] > 80) & (img[:, :, 1] < 200) &  # Medium green
                    (img[:, :, 2] > 150)  # High red
                )

                orange_count = np.sum(orange_mask)

                # If we have a significant number of orange pixels, orbs are present
                # Threshold of 200 catches the HP/run/spec orbs
                return orange_count > 200

        except Exception:
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

    def _is_login_screen(self) -> bool:
        """Check if we're on the login screen by looking for 'Cancel' button.

        The 'Cancel' button only exists on the login screen (not welcome screen),
        making it a reliable indicator.

        Returns:
            True if on login screen, False otherwise
        """
        try:
            from utilities import imagesearch as imsearch

            template_path = LOGIN_IMAGES_PATH / "cancel_button.png"
            if not template_path.exists():
                return False

            result = imsearch.search_img_in_rect(
                str(template_path),
                self.window.rectangle(),
                confidence=0.8,
            )
            return result is not None
        except Exception:
            return False

    def _is_welcome_screen(self) -> bool:
        """Check if we're on the welcome screen.

        The welcome screen has BOTH "New User" AND "Existing User" buttons
        side by side. We require BOTH to be found to avoid false positives
        from individual button templates matching the scroll texture.

        Returns:
            True if on welcome screen, False otherwise
        """
        try:
            from utilities import imagesearch as imsearch

            win_rect = self.window.rectangle()

            # Check for Existing User button
            existing_user_path = LOGIN_IMAGES_PATH / "existing_user_button.png"
            if not existing_user_path.exists():
                return False

            existing_user = imsearch.search_img_in_rect(
                str(existing_user_path),
                win_rect,
                confidence=0.8,
            )

            if not existing_user:
                return False

            # Also verify "New User" button is present (both must exist on welcome)
            new_user_path = LOGIN_IMAGES_PATH / "new_user_button.png"
            if new_user_path.exists():
                new_user = imsearch.search_img_in_rect(
                    str(new_user_path),
                    win_rect,
                    confidence=0.8,
                )
                # Both buttons must be found AND they should be at similar Y position
                # (side by side on the welcome screen)
                if new_user and existing_user:
                    y_diff = abs(new_user.top - existing_user.top)
                    # Buttons should be roughly on the same horizontal line (within 50px)
                    if y_diff < 50:
                        return True

            return False
        except Exception:
            return False

    def get_existing_user_button_location(self) -> Optional["Rectangle"]:
        """Find the 'Existing User' button on the welcome screen.

        Uses template matching to find the button.

        Returns:
            Rectangle of the button, or None if not found
        """
        try:
            from utilities import imagesearch as imsearch

            template_path = LOGIN_IMAGES_PATH / "existing_user_button.png"
            if not template_path.exists():
                return None

            return imsearch.search_img_in_rect(
                str(template_path),
                self.window.rectangle(),
                confidence=0.8,
            )
        except Exception:
            return None

    def get_click_to_play_button_location(self) -> Optional["Rectangle"]:
        """Find the 'Click here to Play' button after login.

        Uses template matching to find the play button that appears
        after successful credential entry.

        Returns:
            Rectangle of the button, or None if not found
        """
        try:
            from utilities import imagesearch as imsearch

            template_path = LOGIN_IMAGES_PATH / "click_to_play.png"
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

    def get_error_message(self) -> Optional[str]:
        """Extract any error message from the login screen.

        Looks for common error text like "Invalid", "Error", etc.

        Returns:
            The error message text, or None if no error visible
        """
        return self._extract_error_text()

    def get_try_again_button_location(self) -> Optional["Rectangle"]:
        """Find the 'Try again' button on the invalid credentials screen.

        This button appears after entering wrong username/password.

        Returns:
            Rectangle of the button, or None if not found
        """
        try:
            from utilities import imagesearch as imsearch

            template_path = LOGIN_IMAGES_PATH / "try_again_button.png"
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

    def is_on_invalid_credentials_screen(self) -> bool:
        """Check if we're on the invalid credentials error screen.

        Returns:
            True if the 'Try again' button is visible, False otherwise
        """
        return self.get_try_again_button_location() is not None

    # Private helper methods

    def _find_login_button_template(self) -> Optional["Rectangle"]:
        """Find login button using template matching."""
        try:
            from utilities import imagesearch as imsearch

            template_path = LOGIN_IMAGES_PATH / "login_button.png"
            if not template_path.exists():
                return None

            # Use higher confidence (0.9) to avoid false matches
            return imsearch.search_img_in_rect(
                str(template_path),
                self.window.rectangle(),
                confidence=0.9,
            )
        except Exception:
            return None

    def _find_welcome_screen_template(self) -> Optional["Rectangle"]:
        """Find welcome screen elements using template matching.

        Looks for either the 'Existing User' button or 'Welcome to RuneScape' text.
        These indicate we're on the initial login screen before entering credentials.
        """
        try:
            from utilities import imagesearch as imsearch

            client_rect = self.window.rectangle()

            # Try to find "Existing User" button
            existing_user_path = LOGIN_IMAGES_PATH / "existing_user_button.png"
            if existing_user_path.exists():
                result = imsearch.search_img_in_rect(
                    str(existing_user_path),
                    client_rect,
                    confidence=0.8,
                )
                if result:
                    return result

            # Try to find "Welcome to RuneScape" text
            welcome_path = LOGIN_IMAGES_PATH / "welcome_to_runescape.png"
            if welcome_path.exists():
                result = imsearch.search_img_in_rect(
                    str(welcome_path),
                    client_rect,
                    confidence=0.8,
                )
                if result:
                    return result

            return None
        except Exception:
            return None

    def _detect_login_screen_ocr(self) -> bool:
        """Detect login screen using OCR.

        Looks for text that indicates we're on a login-related screen:
        - "username" - login form with username field
        - "existing user" - initial welcome screen
        - "new user" - initial welcome screen
        - "welcome to runescape" - initial welcome screen
        """
        try:
            from utilities import ocr
            import utilities.color as clr

            client_rect = self.window.rectangle()
            text = ocr.extract_text(client_rect, ocr.PLAIN_12, [clr.WHITE])
            text_lower = text.lower()

            # Check for any login screen indicators
            login_indicators = [
                "username",
                "existing user",
                "new user",
                "welcome to runescape",
            ]
            return any(indicator in text_lower for indicator in login_indicators)
        except Exception:
            return False

    def _find_username_field(self) -> Optional["Rectangle"]:
        """Find username input field by locating 'Username:' label."""
        try:
            from utilities import ocr
            import utilities.color as clr
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
            import utilities.color as clr

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
