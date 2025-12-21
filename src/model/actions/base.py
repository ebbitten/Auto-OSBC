"""Base types and utilities for the actions module.

This module defines the core types used by all actions:
- ActionResult: Enum for action outcomes (SUCCESS, FAILED, TIMEOUT, etc.)
- ActionOutcome: Dataclass containing result, message, and optional data
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional


class ActionResult(Enum):
    """Possible outcomes for an action."""

    SUCCESS = auto()
    """Action completed successfully."""

    FAILED = auto()
    """Action failed (e.g., couldn't find target)."""

    TIMEOUT = auto()
    """Action timed out waiting for a condition."""

    SAFETY_STOP = auto()
    """Action stopped due to safety condition (friends nearby, etc.)."""

    SKIPPED = auto()
    """Action was skipped (e.g., inventory not full, no need to drop)."""


@dataclass
class ActionOutcome:
    """Result of an action execution.

    Attributes:
        result: The ActionResult enum value
        message: Human-readable description of the outcome
        data: Optional dictionary of additional data (e.g., items found, count)
    """

    result: ActionResult
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if the action was successful."""
        return self.result == ActionResult.SUCCESS

    @property
    def failed(self) -> bool:
        """Check if the action failed."""
        return self.result == ActionResult.FAILED

    @property
    def timed_out(self) -> bool:
        """Check if the action timed out."""
        return self.result == ActionResult.TIMEOUT

    @property
    def safety_stopped(self) -> bool:
        """Check if the action was stopped for safety."""
        return self.result == ActionResult.SAFETY_STOP

    @property
    def skipped(self) -> bool:
        """Check if the action was skipped."""
        return self.result == ActionResult.SKIPPED

    @classmethod
    def ok(cls, message: str = "Success", **data) -> "ActionOutcome":
        """Create a successful outcome."""
        return cls(ActionResult.SUCCESS, message, data)

    @classmethod
    def fail(cls, message: str = "Failed", **data) -> "ActionOutcome":
        """Create a failed outcome."""
        return cls(ActionResult.FAILED, message, data)

    @classmethod
    def timeout(cls, message: str = "Timed out", **data) -> "ActionOutcome":
        """Create a timeout outcome."""
        return cls(ActionResult.TIMEOUT, message, data)

    @classmethod
    def safety(cls, message: str = "Stopped for safety", **data) -> "ActionOutcome":
        """Create a safety stop outcome."""
        return cls(ActionResult.SAFETY_STOP, message, data)

    @classmethod
    def skip(cls, message: str = "Skipped", **data) -> "ActionOutcome":
        """Create a skipped outcome."""
        return cls(ActionResult.SKIPPED, message, data)

    def __str__(self) -> str:
        """String representation for logging."""
        return f"[{self.result.name}] {self.message}"
