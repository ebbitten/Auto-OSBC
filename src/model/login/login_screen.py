"""Login screen detection and state management.

Provides functionality to detect the current state of the game's
login screen and locate UI elements for automated login.
"""

import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np

from utilities.imagesearch import CONFIDENCE_LOOSE

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
        # Screenshot cache for efficient multi-template detection
        self._cached_screenshot: Optional[np.ndarray] = None
        self._cached_win_rect: Optional["Rectangle"] = None
        self._cache_time: float = 0.0

    def _get_screenshot(self, max_age_ms: float = 200) -> tuple[np.ndarray, "Rectangle"]:
        """Get cached screenshot or capture a new one.

        Args:
            max_age_ms: Maximum age of cached screenshot in milliseconds.

        Returns:
            Tuple of (screenshot as numpy array, window rectangle).
        """
        now = time.time() * 1000
        if (
            self._cached_screenshot is None
            or self._cached_win_rect is None
            or (now - self._cache_time) > max_age_ms
        ):
            self._cached_win_rect = self.window.rectangle()
            self._cached_screenshot = self._cached_win_rect.screenshot()
            self._cache_time = now
        return self._cached_screenshot, self._cached_win_rect

    def _clear_screenshot_cache(self) -> None:
        """Clear the screenshot cache."""
        self._cached_screenshot = None
        self._cached_win_rect = None

    def _get_center_region(self, margin_percent: float = 0.2) -> tuple[int, int, int, int]:
        """Get the center region of the window, excluding edges.

        Login buttons are always in the center of the screen, not in the
        inventory area (right side) or chat area (bottom). This prevents
        false positives from template matching against game UI elements.

        Args:
            margin_percent: Percentage of screen to exclude from each edge.
                           0.2 = exclude 20% from each side = center 60%.

        Returns:
            Tuple of (x_offset, y_offset, width, height) relative to screenshot.
        """
        screenshot, win_rect = self._get_screenshot()
        full_width = screenshot.shape[1]
        full_height = screenshot.shape[0]

        x_margin = int(full_width * margin_percent)
        y_margin = int(full_height * margin_percent)

        return (
            x_margin,
            y_margin,
            full_width - (2 * x_margin),
            full_height - (2 * y_margin),
        )

    def _search_template(
        self,
        template_path: Path,
        confidence: float = CONFIDENCE_LOOSE,
        use_center_region: bool = False,
    ) -> Optional["Rectangle"]:
        """Search for a template using cached screenshot.

        Args:
            template_path: Path to the template image.
            confidence: Match confidence threshold.
            use_center_region: If True, only search center 60% of screen.
                              Prevents false positives in inventory/chat areas.

        Returns:
            Rectangle of the found template, or None.
        """
        if not template_path.exists():
            return None

        try:
            from utilities import imagesearch as imsearch
            from utilities.geometry import Rectangle

            screenshot, win_rect = self._get_screenshot()

            # Optionally constrain search to center region
            x_offset, y_offset = 0, 0
            if use_center_region:
                x_offset, y_offset, region_w, region_h = self._get_center_region()
                screenshot = screenshot[
                    y_offset : y_offset + region_h,
                    x_offset : x_offset + region_w,
                ]

            # Search in (possibly cropped) screenshot
            result = imsearch.search_img_in_rect(
                str(template_path),
                screenshot,
                confidence=confidence,
            )

            # Adjust coordinates to be relative to screen
            if result is not None:
                result.left += win_rect.left + x_offset
                result.top += win_rect.top + y_offset

            return result
        except Exception:
            return None

    def detect_state(self) -> LoginScreenInfo:
        """Detect the current login screen state.

        Returns:
            LoginScreenInfo with current state and field locations

        Note:
            Detection order - LOGGED_IN checked first to avoid false positives:
            1. LOGGED_IN - check for inventory/minimap first (avoids template false matches)
            2. WELCOME_SCREEN - structural validation (both buttons at same Y)
            3. LOGIN_SCREEN - login button + cancel button present
            4. CLICK_TO_PLAY - post-login state
        """
        # Clear screenshot cache at start of detection cycle
        # All template searches will use the same screenshot
        self._clear_screenshot_cache()

        # 1. Check if already logged in FIRST
        # This prevents false positives from welcome/login templates matching game UI
        if self.is_logged_in():
            return LoginScreenInfo(state=LoginState.LOGGED_IN)

        # 2. Check for WELCOME_SCREEN using structural validation
        # Requires BOTH buttons at same Y position
        welcome_info = self._check_welcome_screen()
        if welcome_info is not None:
            return LoginScreenInfo(
                state=LoginState.WELCOME_SCREEN,
                existing_user_button=welcome_info,
            )

        # 3. Check for LOGIN_SCREEN (has Login button AND Cancel button)
        # Cancel button distinguishes login from welcome screen
        login_button = self.get_login_button_location()
        if login_button and self._is_login_screen():
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

        # 4. Check for "Click to Play" button (post-login state)
        play_button = self.get_click_to_play_button_location()
        if play_button:
            return LoginScreenInfo(
                state=LoginState.CLICK_TO_PLAY,
                play_button=play_button,
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
        return self._search_template(
            LOGIN_IMAGES_PATH / "cancel_button.png",
            use_center_region=True,
        ) is not None

    def _is_welcome_screen(self) -> bool:
        """Check if we're on the welcome screen.

        Returns:
            True if on welcome screen, False otherwise
        """
        return self._check_welcome_screen() is not None

    def _check_welcome_screen(self) -> Optional["Rectangle"]:
        """Check if we're on the welcome screen and return the Existing User button.

        The welcome screen has BOTH "New User" AND "Existing User" buttons
        side by side at the SAME Y position. This structural validation is
        more reliable than template matching alone.

        Returns:
            Rectangle of the Existing User button if on welcome screen, None otherwise.
            This eliminates the need to search for the button again.
        """
        try:
            # Check for Existing User button (center region only - not in inventory)
            existing_user = self._search_template(
                LOGIN_IMAGES_PATH / "existing_user_button.png",
                use_center_region=True,
            )
            if not existing_user:
                return None

            # Also verify "New User" button is present (both must exist on welcome)
            new_user = self._search_template(
                LOGIN_IMAGES_PATH / "new_user_button.png",
                use_center_region=True,
            )
            if not new_user:
                return None

            # STRUCTURAL VALIDATION: Both buttons must be at similar Y position
            # This is the key check - on welcome screen they're side by side
            y_diff = abs(new_user.top - existing_user.top)
            if y_diff < 50:
                return existing_user  # Return the button we found!

            return None
        except Exception:
            return None

    def get_existing_user_button_location(self) -> Optional["Rectangle"]:
        """Find the 'Existing User' button on the welcome screen.

        Uses template matching to find the button in center region only.

        Returns:
            Rectangle of the button, or None if not found
        """
        return self._search_template(
            LOGIN_IMAGES_PATH / "existing_user_button.png",
            use_center_region=True,
        )

    def get_click_to_play_button_location(self) -> Optional["Rectangle"]:
        """Find the 'Click here to Play' button after login.

        Uses template matching to find the play button that appears
        after successful credential entry (center region only).

        Returns:
            Rectangle of the button, or None if not found
        """
        return self._search_template(
            LOGIN_IMAGES_PATH / "click_to_play.png",
            use_center_region=True,
        )

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
        # Use looser threshold (0.9) to handle button variations
        # Note: 0.9 is MORE permissive than CONFIDENCE_LOOSE (0.8)
        # False positives are prevented by:
        #   1. Center region constraint (not in inventory)
        #   2. _is_login_screen() cancel button check
        return self._search_template(
            LOGIN_IMAGES_PATH / "login_button.png",
            confidence=0.9,
            use_center_region=True,
        )

    def _find_welcome_screen_template(self) -> Optional["Rectangle"]:
        """Find welcome screen elements using template matching.

        Looks for either the 'Existing User' button or 'Welcome to RuneScape' text.
        These indicate we're on the initial login screen before entering credentials.
        Uses center region to avoid false positives in inventory area.
        """
        # Try to find "Existing User" button (center region only)
        result = self._search_template(
            LOGIN_IMAGES_PATH / "existing_user_button.png",
            use_center_region=True,
        )
        if result:
            return result

        # Try to find "Welcome to RuneScape" text (center region only)
        return self._search_template(
            LOGIN_IMAGES_PATH / "welcome_to_runescape.png",
            use_center_region=True,
        )

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
