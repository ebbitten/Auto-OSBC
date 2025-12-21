"""Actions module - reusable, composable action primitives for bot scripts.

This module provides high-level actions that encapsulate common bot behaviors:
- interaction: find_and_interact, click_object
- inventory: manage_if_full, drop_items
- waiting: wait_for_idle, wait_for_action, wait_until
- safety: safe_logout, check_safety_conditions
- combat: attack_npc, eat_food, loot_items

All actions are standalone functions that take a bot instance as the first argument.
Actions return ActionOutcome objects containing:
- Result status (success, fail, skip, timeout, safety)
- Data dict with any intent objects for the Executor to perform

The Intent/Executor pattern separates "what to do" from "doing it":
- Actions analyze state and return intents (ClickIntent, WaitIntent, etc.)
- Executor performs the actual side effects (mouse movement, clicks)
- This enables pure unit testing of bot logic

Usage:
    from model.actions import interaction, inventory, waiting, safety
    from model.actions.executor import Executor

    # In bot main_loop:
    executor = Executor(self)
    result = interaction.find_and_interact(self, clr.PINK)
    if result.success:
        executor.execute(result.data["intent"])
        waiting.wait_for_idle(self)
"""

from .base import ActionOutcome, ActionResult
from . import interaction
from . import inventory
from . import waiting
from . import safety
from . import intents
from .executor import Executor, MockExecutor

__all__ = [
    "ActionResult",
    "ActionOutcome",
    "interaction",
    "inventory",
    "waiting",
    "safety",
    "intents",
    "Executor",
    "MockExecutor",
]
