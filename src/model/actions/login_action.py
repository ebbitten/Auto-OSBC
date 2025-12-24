"""Login action - high-level login automation.

Provides a standalone perform_login() function that can be called
without needing a full Bot instance.
"""

from typing import Optional

from model.actions.base import ActionOutcome
from utilities.window import Window


class _LoginContext:
    """Minimal context for login service.

    Provides the bare minimum interface that LoginService needs:
    - win: Window object
    - log_msg: Logging function
    """

    def __init__(self, window: Window, log_fn=print):
        self.win = window
        self._log_fn = log_fn
        from utilities.mouse import Mouse
        self.mouse = Mouse()

    def log_msg(self, msg: str, **kwargs):
        self._log_fn(f"[LOGIN] {msg}")


def perform_login(
    window_title: str = "RuneLite",
    max_attempts: int = 3,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> ActionOutcome:
    """Perform login on the specified game window.

    This is the main entry point for login automation. It:
    1. Connects to the game window
    2. Checks if already logged in
    3. Detects the login screen
    4. Performs the login sequence

    Args:
        window_title: Title of the game window (default: "RuneLite")
        max_attempts: Maximum login retry attempts (default: 3)
        username: Override username (uses OSBC_USERNAME env var if None)
        password: Override password (uses OSBC_PASSWORD env var if None)

    Returns:
        ActionOutcome with success/failure status
    """
    from model.login.login_service import LoginService, LoginCredentials
    from model.login.login_screen import LoginScreenDetector

    # Check credentials first (before window operations)
    creds = LoginCredentials(username=username, password=password)
    if not creds.is_configured():
        return ActionOutcome.fail(
            "Credentials not configured. Set OSBC_USERNAME and OSBC_PASSWORD environment variables.",
            has_credentials=False,
        )

    # Connect to game window
    try:
        # Default padding for RuneLite: top=26 (title bar)
        win = Window(window_title, padding_top=26, padding_left=0)
        # Note: We don't call initialize() here since login screen doesn't have
        # in-game UI elements (minimap, chat, control panel). The Window class
        # still provides rectangle() and position() without initialization.
        _ = win.rectangle()  # Verify window exists
    except Exception as e:
        return ActionOutcome.fail(
            f"Could not find window '{window_title}': {e}",
            window_found=False,
        )

    # Create login context and detector
    context = _LoginContext(win)
    detector = LoginScreenDetector(win)

    # Check current state
    if detector.is_logged_in():
        return ActionOutcome.ok(
            "Already logged in",
            already_logged_in=True,
        )

    if not detector.is_on_login_screen():
        return ActionOutcome.fail(
            "Not on login screen. Navigate to the login screen first.",
            on_login_screen=False,
        )

    # Perform login
    service = LoginService(context)
    return service.login(
        username=username,
        password=password,
        max_attempts=max_attempts,
    )
