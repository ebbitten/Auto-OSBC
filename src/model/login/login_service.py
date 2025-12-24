"""High-level login orchestration service.

Provides a complete login automation solution including:
- Credential management from environment variables or .env file
- Login screen detection
- Login sequence execution with human-like input
- Error handling and retry logic
"""

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dotenv import load_dotenv

from model.actions.base import ActionOutcome
from model.actions.executor import Executor
from model.actions.intents import (
    ClickIntent,
    CompositeIntent,
    KeyPressIntent,
    SleepIntent,
    TypeIntent,
    WaitIntent,
)
from model.login.login_screen import LoginScreenDetector, LoginScreenInfo, LoginState

if TYPE_CHECKING:
    from model.bot import Bot


class LoginCredentials:
    """Credential management with environment variable support.

    Loads credentials from .env file or environment variables,
    with optional override via constructor parameters.

    Attributes:
        ENV_USERNAME: Name of the username environment variable
        ENV_PASSWORD: Name of the password environment variable
        username: The username to use for login
        password: The password to use for login
    """

    ENV_USERNAME = "OSBC_USERNAME"
    ENV_PASSWORD = "OSBC_PASSWORD"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize credentials.

        Loads from .env file in project root, then checks environment variables.

        Args:
            username: Override username (uses env var if not provided)
            password: Override password (uses env var if not provided)
        """
        # Load .env file from project root
        project_root = Path(__file__).parent.parent.parent.parent
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        self.username = username if username is not None else os.environ.get(self.ENV_USERNAME, "").strip()
        self.password = password if password is not None else os.environ.get(self.ENV_PASSWORD, "").strip()

    def is_configured(self) -> bool:
        """Check if credentials are properly configured.

        Returns:
            True if both username and password are non-empty, False otherwise
        """
        return bool(self.username) and bool(self.password)


class LoginService:
    """Orchestrates the login process for a bot.

    Handles:
    - Credential retrieval from environment
    - Login screen detection
    - Login sequence execution
    - Error handling and retry logic
    - Post-login validation
    """

    def __init__(self, bot: "Bot"):
        """Initialize the login service.

        Args:
            bot: The Bot instance to perform login for
        """
        self.bot = bot
        self.detector = LoginScreenDetector(bot.win)
        self.executor = Executor(bot)
        self.credentials = LoginCredentials()

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_attempts: int = 3,
        timeout: float = 60.0,
    ) -> ActionOutcome:
        """Perform full login sequence.

        Args:
            username: Override username (uses env var if not provided)
            password: Override password (uses env var if not provided)
            max_attempts: Number of retry attempts on failure
            timeout: Maximum time to wait for login completion

        Returns:
            ActionOutcome indicating success or failure
        """
        # Get credentials
        creds = self._get_credentials(username, password)

        # Validate credentials are configured
        if not creds.is_configured():
            return ActionOutcome.fail(
                "Credentials not configured. Set OSBC_USERNAME and OSBC_PASSWORD environment variables.",
                has_credentials=False,
            )

        # Check if already logged in
        if self.detector.is_logged_in():
            return ActionOutcome.ok(
                "Already logged in",
                already_logged_in=True,
            )

        # Check if on login screen
        if not self.detector.is_on_login_screen():
            return ActionOutcome.fail(
                "Not on login screen",
                state="unknown",
            )

        # Handle welcome screen - click "Existing User" first
        state_info = self.detector.detect_state()
        if state_info.state == LoginState.WELCOME_SCREEN:
            result = self._click_existing_user(state_info)
            if not result.success:
                return result
            # Re-detect state after clicking
            time.sleep(1.0)

        # Attempt login with retries
        for attempt in range(max_attempts):
            self.bot.log_msg(f"Login attempt {attempt + 1}/{max_attempts}")

            # Check for login fields
            username_field = self.detector.get_username_field_location()
            password_field = self.detector.get_password_field_location()
            login_button = self.detector.get_login_button_location()

            if username_field is None or login_button is None:
                return ActionOutcome.fail(
                    "Could not find login field or button",
                    username_field_found=username_field is not None,
                    password_field_found=password_field is not None,
                    login_button_found=login_button is not None,
                )

            # Build and execute login sequence
            sequence = self._build_login_sequence(creds.username, creds.password)
            result = self._execute_login_sequence(sequence)

            if result.success:
                self.bot.log_msg("Login successful")
                return ActionOutcome.ok(
                    "Login successful",
                    attempts=attempt + 1,
                )

            # Check if we should retry
            error_message = self.detector.get_error_message()

            if error_message and "invalid" in error_message.lower():
                # Don't retry on invalid credentials
                return ActionOutcome.fail(
                    f"Invalid credentials: {error_message}",
                    attempts=attempt + 1,
                    error_message=error_message,
                )

            # Wait before retry
            if attempt < max_attempts - 1:
                self.bot.log_msg(f"Login failed, retrying in 2 seconds...")
                time.sleep(2)

        return ActionOutcome.fail(
            f"Login failed after {max_attempts} attempts",
            attempts=max_attempts,
        )

    def _get_credentials(
        self,
        username: Optional[str],
        password: Optional[str],
    ) -> LoginCredentials:
        """Get credentials with override support.

        Args:
            username: Override username (None to use env var)
            password: Override password (None to use env var)

        Returns:
            LoginCredentials instance with appropriate values
        """
        if username is not None or password is not None:
            # Use explicit values if provided (even if empty string)
            return LoginCredentials(
                username=username if username is not None else self.credentials.username,
                password=password if password is not None else self.credentials.password,
            )
        return self.credentials

    def _build_login_sequence(
        self,
        username: str,
        password: str,
    ) -> CompositeIntent:
        """Build the composite intent for login sequence.

        Args:
            username: The username to type
            password: The password to type

        Returns:
            CompositeIntent containing the full login sequence
        """
        username_field = self.detector.get_username_field_location()
        password_field = self.detector.get_password_field_location()
        login_button = self.detector.get_login_button_location()

        intents = []

        # Click username field
        if username_field:
            intents.append(
                ClickIntent(
                    point=username_field.random_point(),
                    speed="medium",
                )
            )
            intents.append(SleepIntent(duration=0.2))

        # Type username
        intents.append(
            TypeIntent(
                text=username,
                interval=0.05,
                field_name="username",
                mask_in_logs=False,
            )
        )

        # Tab to password field (or click it)
        intents.append(KeyPressIntent(key="tab"))
        intents.append(SleepIntent(duration=0.2))

        # Type password (masked in logs)
        intents.append(
            TypeIntent(
                text=password,
                interval=0.05,
                field_name="password",
                mask_in_logs=True,
            )
        )

        # Click login button
        if login_button:
            intents.append(SleepIntent(duration=0.2))
            intents.append(
                ClickIntent(
                    point=login_button.random_point(),
                    speed="medium",
                )
            )

        # Wait for login to complete
        intents.append(
            WaitIntent(
                condition=self.detector.is_logged_in,
                timeout=30.0,
                poll_interval=0.5,
                description="waiting for login to complete",
            )
        )

        return CompositeIntent(intents=intents)

    def _execute_login_sequence(self, sequence: CompositeIntent) -> ActionOutcome:
        """Execute the login intent sequence.

        Args:
            sequence: The CompositeIntent to execute

        Returns:
            ActionOutcome from the executor
        """
        return self.executor.execute(sequence)

    def _click_existing_user(self, state_info: LoginScreenInfo) -> ActionOutcome:
        """Click the 'Existing User' button on the welcome screen.

        Args:
            state_info: LoginScreenInfo containing the button location

        Returns:
            ActionOutcome indicating success or failure
        """
        if not state_info.existing_user_button:
            return ActionOutcome.fail(
                "Existing User button not found",
                state="welcome_screen",
            )

        self.bot.log_msg("Clicking 'Existing User' button")

        # Build click intent
        click_intent = ClickIntent(
            point=state_info.existing_user_button.random_point(),
            speed="medium",
        )

        # Execute click
        result = self.executor.execute(click_intent)

        if result.success:
            return ActionOutcome.ok("Clicked Existing User button")
        else:
            return ActionOutcome.fail(
                f"Failed to click Existing User button: {result.message}",
            )
