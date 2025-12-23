"""Login automation module.

Provides automated login functionality for the game client using
human-like input via the intent-executor pattern.
"""

from .login_screen import LoginState, LoginScreenInfo, LoginScreenDetector
from .login_service import LoginCredentials, LoginService

__all__ = [
    "LoginState",
    "LoginScreenInfo",
    "LoginScreenDetector",
    "LoginCredentials",
    "LoginService",
]
