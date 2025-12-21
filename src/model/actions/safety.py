"""Safety action primitives for bot scripts.

This module provides reusable functions for safety checks
and safe shutdown procedures.

Safety actions return intents for the Executor to perform (logout, stop, etc.).
Query functions (check_safety_conditions, friends_nearby) are pure.
"""

from typing import TYPE_CHECKING, Optional

from .base import ActionOutcome
from .intents import CompositeIntent, LogMessageIntent, LogoutIntent, StopIntent

if TYPE_CHECKING:
    from model.bot import Bot


def check_safety_conditions(
    bot: "Bot",
    logout_on_friends: bool = True,
) -> Optional[str]:
    """
    Check all safety conditions and return reason if any triggered.

    This is a simple check function that returns a reason string
    if any safety condition is triggered, or None if all is well.

    No intent is returned - this is a pure query.

    Args:
        bot: The bot instance
        logout_on_friends: Whether to check for friends nearby

    Returns:
        Reason string if safety condition triggered, None otherwise
    """
    if logout_on_friends and bot.friends_nearby():
        return "Friends nearby"

    return None


def safe_logout(
    bot: "Bot",
    reason: str = "Safety stop",
) -> ActionOutcome:
    """
    Return intents to safely logout and stop the bot.

    Combines logging, logout, and stop into one composite intent.
    This is the recommended way to end a bot session.

    Args:
        bot: The bot instance (not used, kept for API compatibility)
        reason: Reason for logging out (will be logged)

    Returns:
        ActionOutcome.safety() with intent=CompositeIntent
    """
    intent = CompositeIntent(
        intents=[
            LogMessageIntent(message=reason),
            LogoutIntent(reason=reason),
            StopIntent(reason=reason),
        ]
    )

    return ActionOutcome.safety(
        reason,
        intent=intent,
        logged_out=True,
        stopped=True,
    )


def check_and_logout_if_unsafe(
    bot: "Bot",
    logout_on_friends: bool = True,
) -> ActionOutcome:
    """
    Check safety conditions and return logout intent if any triggered.

    Combines check_safety_conditions and safe_logout into one action.
    Use this in the main loop to handle safety in one call.

    Args:
        bot: The bot instance
        logout_on_friends: Whether to check for friends nearby

    Returns:
        ActionOutcome.safety() with intent if unsafe
        ActionOutcome.ok() with safe=True if all conditions passed
    """
    reason = check_safety_conditions(bot, logout_on_friends)

    if reason:
        return safe_logout(bot, reason)

    return ActionOutcome.ok(
        "Safety conditions passed",
        safe=True,
    )


def friends_nearby(bot: "Bot") -> ActionOutcome:
    """
    Check if friends are nearby on the minimap.

    No intent is returned - this is a pure query.

    Args:
        bot: The bot instance

    Returns:
        ActionOutcome.ok() with friends_nearby data
    """
    nearby = bot.friends_nearby()

    return ActionOutcome.ok(
        f"Friends {'detected' if nearby else 'not detected'}",
        friends_nearby=nearby,
    )


def logout_with_reason(
    bot: "Bot",
    reason: str,
) -> ActionOutcome:
    """
    Return an intent to logout the bot with a specific reason (without stopping).

    Use this when you want to logout but potentially
    restart or continue later.

    Args:
        bot: The bot instance (not used, kept for API compatibility)
        reason: Reason for logging out

    Returns:
        ActionOutcome.ok() with intent=CompositeIntent
    """
    intent = CompositeIntent(
        intents=[
            LogMessageIntent(message=reason),
            LogoutIntent(reason=reason),
        ]
    )

    return ActionOutcome.ok(
        f"Logout intent: {reason}",
        intent=intent,
        reason=reason,
        logged_out=True,
    )


def stop_bot(
    bot: "Bot",
    reason: str = "Bot stopped",
) -> ActionOutcome:
    """
    Return an intent to stop the bot (without logging out first).

    Use this for emergency stops or when logout isn't needed.

    Args:
        bot: The bot instance (not used, kept for API compatibility)
        reason: Reason for stopping

    Returns:
        ActionOutcome.ok() with intent=CompositeIntent
    """
    intent = CompositeIntent(
        intents=[
            LogMessageIntent(message=reason),
            StopIntent(reason=reason),
        ]
    )

    return ActionOutcome.ok(
        f"Stop intent: {reason}",
        intent=intent,
        reason=reason,
        stopped=True,
    )


def handle_failure_limit(
    bot: "Bot",
    failures: int,
    limit: int,
    failure_type: str = "search",
) -> ActionOutcome:
    """
    Handle failure count reaching limit by returning logout intent.

    Common pattern: if something fails too many times in a row,
    safely logout rather than continuing in a broken state.

    Args:
        bot: The bot instance
        failures: Current failure count
        limit: Maximum allowed failures
        failure_type: Description of what's failing (for logging)

    Returns:
        ActionOutcome.safety() with intent if limit exceeded
        ActionOutcome.ok() with exceeded=False if under limit
    """
    if failures > limit:
        reason = f"Too many {failure_type} failures ({failures}/{limit})"
        return safe_logout(bot, reason)

    return ActionOutcome.ok(
        f"{failure_type} failures: {failures}/{limit}",
        exceeded=False,
        failures=failures,
        limit=limit,
    )


def ensure_safe_state(
    bot: "Bot",
    logout_on_friends: bool = True,
    max_failures: Optional[int] = None,
    current_failures: int = 0,
    failure_type: str = "search",
) -> ActionOutcome:
    """
    Comprehensive safety check combining multiple conditions.

    This is a convenience function that checks multiple safety
    conditions in one call. Use this at the start of each
    main loop iteration.

    Args:
        bot: The bot instance
        logout_on_friends: Whether to check for friends nearby
        max_failures: Maximum allowed consecutive failures (None to skip)
        current_failures: Current failure count
        failure_type: Description of failure type

    Returns:
        ActionOutcome.safety() with intent if any condition triggered
        ActionOutcome.ok() with safe=True if all passed
    """
    # Check friends nearby
    if logout_on_friends and bot.friends_nearby():
        return safe_logout(bot, "Friends nearby")

    # Check failure limit
    if max_failures is not None and current_failures > max_failures:
        reason = f"Too many {failure_type} failures ({current_failures}/{max_failures})"
        return safe_logout(bot, reason)

    return ActionOutcome.ok(
        "All safety conditions passed",
        safe=True,
        friends_checked=logout_on_friends,
        failures_checked=max_failures is not None,
    )
