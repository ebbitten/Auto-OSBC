"""Executor for intent-based actions.

The Executor takes intents (what to do) and performs the actual side effects
(mouse movement, clicks, keyboard input, etc.).

This separation allows bot logic to be fully unit-tested without mocking
the mouse/keyboard interfaces.
"""

import time
from typing import TYPE_CHECKING

from .base import ActionOutcome
from .intents import (
    ClickIntent,
    CompositeIntent,
    DropIntent,
    DropSlotsIntent,
    Intent,
    LogMessageIntent,
    LogoutIntent,
    MoveIntent,
    SleepIntent,
    StopIntent,
    WaitIntent,
)

if TYPE_CHECKING:
    from model.bot import Bot


class Executor:
    """Executes intents by performing actual side effects.

    The Executor is the bridge between pure bot logic (which produces intents)
    and the actual game automation (mouse, keyboard, etc.).

    Usage:
        executor = Executor(bot)
        result = executor.execute(ClickIntent(point=(100, 200)))
    """

    def __init__(self, bot: "Bot"):
        """Initialize the executor with a bot instance.

        Args:
            bot: The Bot instance that provides access to mouse, window, etc.
        """
        self.bot = bot

    def execute(self, intent: Intent) -> ActionOutcome:
        """Execute an intent and return the result.

        Args:
            intent: The intent to execute

        Returns:
            ActionOutcome describing the result of execution
        """
        if isinstance(intent, ClickIntent):
            return self._execute_click(intent)
        elif isinstance(intent, MoveIntent):
            return self._execute_move(intent)
        elif isinstance(intent, WaitIntent):
            return self._execute_wait(intent)
        elif isinstance(intent, SleepIntent):
            return self._execute_sleep(intent)
        elif isinstance(intent, DropIntent):
            return self._execute_drop(intent)
        elif isinstance(intent, DropSlotsIntent):
            return self._execute_drop_slots(intent)
        elif isinstance(intent, LogoutIntent):
            return self._execute_logout(intent)
        elif isinstance(intent, StopIntent):
            return self._execute_stop(intent)
        elif isinstance(intent, LogMessageIntent):
            return self._execute_log_message(intent)
        elif isinstance(intent, CompositeIntent):
            return self._execute_composite(intent)
        else:
            return ActionOutcome.fail(
                f"Unknown intent type: {type(intent).__name__}",
                intent_type=type(intent).__name__,
            )

    def _execute_click(self, intent: ClickIntent) -> ActionOutcome:
        """Execute a click intent."""
        from utilities.geometry import Point

        target = Point(*intent.point)
        self.bot.mouse.move_to(target, mouseSpeed=intent.speed)

        if intent.right_click:
            self.bot.mouse.right_click()
        else:
            self.bot.mouse.click()

        return ActionOutcome.ok(
            f"Clicked at ({intent.point[0]}, {intent.point[1]})",
            point=intent.point,
            right_click=intent.right_click,
        )

    def _execute_move(self, intent: MoveIntent) -> ActionOutcome:
        """Execute a move intent (no click)."""
        from utilities.geometry import Point

        target = Point(*intent.point)
        self.bot.mouse.move_to(target, mouseSpeed=intent.speed)

        return ActionOutcome.ok(
            f"Moved to ({intent.point[0]}, {intent.point[1]})",
            point=intent.point,
        )

    def _execute_wait(self, intent: WaitIntent) -> ActionOutcome:
        """Execute a wait intent by polling the condition."""
        start_time = time.time()

        while time.time() - start_time < intent.timeout:
            if intent.condition():
                elapsed = time.time() - start_time
                return ActionOutcome.ok(
                    f"Wait completed: {intent.description}",
                    elapsed_seconds=elapsed,
                    description=intent.description,
                )
            time.sleep(intent.poll_interval)

        elapsed = time.time() - start_time
        return ActionOutcome.timeout(
            f"Wait timed out: {intent.description}",
            elapsed_seconds=elapsed,
            timeout_seconds=intent.timeout,
            description=intent.description,
        )

    def _execute_sleep(self, intent: SleepIntent) -> ActionOutcome:
        """Execute a simple sleep intent."""
        time.sleep(intent.duration)
        return ActionOutcome.ok(
            f"Slept for {intent.duration}s",
            duration=intent.duration,
        )

    def _execute_drop(self, intent: DropIntent) -> ActionOutcome:
        """Execute a drop all intent."""
        initial_count = self.bot.count_inventory_items_visual()

        self.bot.drop_all(skip_rows=intent.skip_rows, skip_slots=intent.skip_slots)

        # Small delay for animation
        time.sleep(0.5)

        final_count = self.bot.count_inventory_items_visual()
        dropped_count = initial_count - final_count

        return ActionOutcome.ok(
            f"Dropped {dropped_count} items",
            initial_count=initial_count,
            final_count=final_count,
            dropped_count=dropped_count,
            skip_slots=intent.skip_slots,
            skip_rows=intent.skip_rows,
        )

    def _execute_drop_slots(self, intent: DropSlotsIntent) -> ActionOutcome:
        """Execute a drop specific slots intent."""
        if not intent.slots:
            return ActionOutcome.skip(
                "No slots specified to drop",
                slots=[],
            )

        initial_count = self.bot.count_inventory_items_visual()
        self.bot.drop(intent.slots)

        # Small delay for animation
        time.sleep(0.3)

        final_count = self.bot.count_inventory_items_visual()
        dropped_count = initial_count - final_count

        return ActionOutcome.ok(
            f"Dropped {dropped_count} items from specified slots",
            slots=intent.slots,
            initial_count=initial_count,
            final_count=final_count,
            dropped_count=dropped_count,
        )

    def _execute_logout(self, intent: LogoutIntent) -> ActionOutcome:
        """Execute a logout intent."""
        self.bot.log_msg(intent.reason)
        self.bot.logout()

        return ActionOutcome.ok(
            f"Logged out: {intent.reason}",
            reason=intent.reason,
            logged_out=True,
        )

    def _execute_stop(self, intent: StopIntent) -> ActionOutcome:
        """Execute a stop intent."""
        self.bot.log_msg(intent.reason)
        self.bot.stop()

        return ActionOutcome.ok(
            f"Stopped: {intent.reason}",
            reason=intent.reason,
            stopped=True,
        )

    def _execute_log_message(self, intent: LogMessageIntent) -> ActionOutcome:
        """Execute a log message intent."""
        self.bot.log_msg(intent.message)

        return ActionOutcome.ok(
            f"Logged: {intent.message}",
            message=intent.message,
        )

    def _execute_composite(self, intent: CompositeIntent) -> ActionOutcome:
        """Execute a composite intent by running each sub-intent in order."""
        results = []

        for i, sub_intent in enumerate(intent.intents):
            result = self.execute(sub_intent)
            results.append(result)

            # Stop on failure
            if result.failed:
                return ActionOutcome.fail(
                    f"Composite intent failed at step {i + 1}: {result.message}",
                    step=i + 1,
                    failed_intent=type(sub_intent).__name__,
                    results=results,
                )

        return ActionOutcome.ok(
            f"Executed {len(intent.intents)} intents",
            count=len(intent.intents),
            results=results,
        )


class MockExecutor(Executor):
    """Mock executor for testing that records intents without executing them.

    Usage in tests:
        executor = MockExecutor(mock_bot)
        executor.execute(ClickIntent(point=(100, 200)))
        assert executor.executed_intents[0] == ClickIntent(point=(100, 200))
    """

    def __init__(self, bot: "Bot" = None):
        """Initialize the mock executor.

        Args:
            bot: Optional bot instance (not used in mock, but kept for API compatibility)
        """
        self.bot = bot
        self.executed_intents: list = []

    def execute(self, intent: Intent) -> ActionOutcome:
        """Record the intent without executing it.

        Args:
            intent: The intent to record

        Returns:
            ActionOutcome.ok() indicating success (mock always succeeds)
        """
        self.executed_intents.append(intent)
        return ActionOutcome.ok(
            f"Mock executed: {type(intent).__name__}",
            intent_type=type(intent).__name__,
        )

    def clear(self):
        """Clear the list of executed intents."""
        self.executed_intents = []

    def get_clicks(self) -> list:
        """Get all ClickIntent objects that were executed."""
        return [i for i in self.executed_intents if isinstance(i, ClickIntent)]

    def get_waits(self) -> list:
        """Get all WaitIntent objects that were executed."""
        return [i for i in self.executed_intents if isinstance(i, WaitIntent)]

    def get_drops(self) -> list:
        """Get all DropIntent objects that were executed."""
        return [i for i in self.executed_intents if isinstance(i, DropIntent)]
