"""Visual detection tests using real screenshot fixtures.

These tests validate that LoginScreenDetector correctly identifies
login states from actual game screenshots, not just mocked responses.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import cv2
import numpy as np

# Fixture path
FIXTURES_PATH = Path(__file__).parent.parent / "fixtures" / "login_states"


def load_fixture(name: str) -> np.ndarray:
    """Load a screenshot fixture."""
    path = FIXTURES_PATH / name
    if not path.exists():
        pytest.skip(f"Fixture not found: {name}")
    img = cv2.imread(str(path))
    if img is None:
        pytest.skip(f"Could not load fixture: {name}")
    return img


class MockWindow:
    """Mock window that returns fixture screenshots."""

    def __init__(self, screenshot: np.ndarray):
        self._screenshot = screenshot
        self._rect = MagicMock()
        self._rect.left = 0
        self._rect.top = 0
        self._rect.width = screenshot.shape[1]
        self._rect.height = screenshot.shape[0]
        self._rect.screenshot.return_value = screenshot
        self.inventory_slots = None

    def rectangle(self):
        return self._rect

    def initialize(self):
        # Simulate failed initialization (not logged in)
        raise Exception("Not logged in - no game UI found")

    def focus(self):
        pass


class MockWindowLoggedIn(MockWindow):
    """Mock window that simulates logged-in state."""

    def __init__(self, screenshot: np.ndarray):
        super().__init__(screenshot)
        self.inventory_slots = [MagicMock()] * 28  # 28 inventory slots

    def initialize(self):
        # Simulate successful initialization (logged in)
        pass


class TestLoginDetectionWithFixtures:
    """Test login detection using real screenshot fixtures."""

    def test_fixture_files_exist(self):
        """Verify required fixture files are present."""
        assert FIXTURES_PATH.exists(), f"Fixtures path not found: {FIXTURES_PATH}"

        required_fixtures = [
            "welcome_screen.png",
            "login_screen.png",
            "logged_in_screen.png",
        ]

        for fixture in required_fixtures:
            path = FIXTURES_PATH / fixture
            assert path.exists(), f"Missing fixture: {fixture}"

    def test_detect_welcome_screen(self):
        """Test detection of WELCOME screen from fixture."""
        from model.login.login_screen import LoginScreenDetector, LoginState

        screenshot = load_fixture("welcome_screen.png")
        mock_window = MockWindow(screenshot)

        detector = LoginScreenDetector(mock_window)
        state_info = detector.detect_state()

        assert state_info.state == LoginState.WELCOME_SCREEN, (
            f"Expected WELCOME_SCREEN, got {state_info.state.name}"
        )
        assert state_info.existing_user_button is not None, (
            "Should find 'Existing User' button on welcome screen"
        )

    def test_detect_login_screen(self):
        """Test detection of LOGIN screen from fixture."""
        from model.login.login_screen import LoginScreenDetector, LoginState

        screenshot = load_fixture("login_screen.png")
        mock_window = MockWindow(screenshot)

        detector = LoginScreenDetector(mock_window)
        state_info = detector.detect_state()

        assert state_info.state == LoginState.LOGIN_SCREEN, (
            f"Expected LOGIN_SCREEN, got {state_info.state.name}"
        )

    def test_detect_logged_in_screen(self):
        """Test detection of LOGGED_IN screen from fixture.

        This is the critical test - the detector should NOT falsely
        detect WELCOME_SCREEN when the player is actually logged in.
        """
        from model.login.login_screen import LoginScreenDetector, LoginState

        screenshot = load_fixture("logged_in_screen.png")
        # Use MockWindowLoggedIn which simulates successful initialize()
        mock_window = MockWindowLoggedIn(screenshot)

        detector = LoginScreenDetector(mock_window)
        state_info = detector.detect_state()

        assert state_info.state == LoginState.LOGGED_IN, (
            f"Expected LOGGED_IN, got {state_info.state.name}. "
            "This was the bug we fixed - template matching was falsely "
            "detecting 'Existing User' button in inventory area."
        )

    def test_no_false_positive_on_logged_in(self):
        """Ensure no false positive WELCOME detection on logged-in screen.

        This test specifically guards against the regression where
        inventory slots were matching the 'Existing User' button template.
        """
        from model.login.login_screen import LoginScreenDetector, LoginState

        screenshot = load_fixture("logged_in_screen.png")
        mock_window = MockWindowLoggedIn(screenshot)

        detector = LoginScreenDetector(mock_window)
        state_info = detector.detect_state()

        # Should NOT be WELCOME_SCREEN
        assert state_info.state != LoginState.WELCOME_SCREEN, (
            "False positive: Detected WELCOME_SCREEN on logged-in screenshot. "
            "The 'Existing User' button template is matching something else."
        )

        # Should NOT be LOGIN_SCREEN
        assert state_info.state != LoginState.LOGIN_SCREEN, (
            "False positive: Detected LOGIN_SCREEN on logged-in screenshot."
        )


class TestTemplateMatchingOnFixtures:
    """Test individual template matching methods on fixtures."""

    def test_existing_user_button_on_welcome(self):
        """Verify 'Existing User' button is found on welcome screen."""
        from model.login.login_screen import LoginScreenDetector

        screenshot = load_fixture("welcome_screen.png")
        mock_window = MockWindow(screenshot)

        detector = LoginScreenDetector(mock_window)
        button = detector.get_existing_user_button_location()

        assert button is not None, "Should find 'Existing User' button"
        assert button.width > 50, "Button should have reasonable width"
        assert button.height > 20, "Button should have reasonable height"

    def test_structural_validation_weakness(self):
        """Document that structural validation alone has false positives.

        This test documents the known issue: the structural validation
        (_check_welcome_screen) can still find matches on logged-in screens.
        The fix is to check is_logged_in() FIRST in detect_state().

        This is NOT a failure - it's documenting the weakness that
        necessitated the detection order fix.
        """
        from model.login.login_screen import LoginScreenDetector

        screenshot = load_fixture("logged_in_screen.png")
        mock_window = MockWindowLoggedIn(screenshot)

        detector = LoginScreenDetector(mock_window)

        # The structural validation MAY find false matches
        # This is expected - it's why we check is_logged_in() first
        welcome_info = detector._check_welcome_screen()

        # Document the current behavior (may or may not find match)
        if welcome_info is not None:
            # This is the known weakness we identified in 5 Whys
            # The template matching is too permissive
            pass  # Expected - structural validation is imperfect

        # The REAL protection is that detect_state() checks is_logged_in() first
        state_info = detector.detect_state()
        assert state_info.state.name == "LOGGED_IN", (
            "Even if structural validation finds a match, detect_state() "
            "should return LOGGED_IN because is_logged_in() is checked first."
        )

    def test_cancel_button_on_login_screen(self):
        """Verify 'Cancel' button is found on login screen."""
        from model.login.login_screen import LoginScreenDetector

        screenshot = load_fixture("login_screen.png")
        mock_window = MockWindow(screenshot)

        detector = LoginScreenDetector(mock_window)
        is_login = detector._is_login_screen()

        assert is_login, "Should detect login screen via Cancel button"


@pytest.mark.skipif(
    not (FIXTURES_PATH / "click_to_play_screen.png").exists(),
    reason="CLICK_TO_PLAY fixture not available"
)
class TestClickToPlayDetection:
    """Test CLICK_TO_PLAY detection (when fixture available)."""

    def test_detect_click_to_play_screen(self):
        """Test detection of CLICK_TO_PLAY screen from fixture."""
        from model.login.login_screen import LoginScreenDetector, LoginState

        screenshot = load_fixture("click_to_play_screen.png")
        mock_window = MockWindow(screenshot)

        detector = LoginScreenDetector(mock_window)
        state_info = detector.detect_state()

        assert state_info.state == LoginState.CLICK_TO_PLAY
        assert state_info.play_button is not None
