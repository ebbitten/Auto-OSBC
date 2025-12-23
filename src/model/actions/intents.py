"""Intent types for the action system.

Intents represent "what to do" without actually performing side effects.
They are executed by an Executor, which handles the actual mouse/keyboard input.

This separation enables:
- Pure unit testing of bot logic without mocking side effects
- Easy inspection and logging of what actions would be performed
- Potential replay/recording of action sequences
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Union


@dataclass
class ClickIntent:
    """Intent to click at a screen position.

    Attributes:
        point: (x, y) screen coordinates to click
        speed: Mouse movement speed ("slowest", "slow", "medium", "fast", "fastest")
        right_click: Whether to right-click instead of left-click
    """

    point: Tuple[int, int]
    speed: str = "medium"
    right_click: bool = False


@dataclass
class MoveIntent:
    """Intent to move mouse without clicking.

    Attributes:
        point: (x, y) screen coordinates to move to
        speed: Mouse movement speed
    """

    point: Tuple[int, int]
    speed: str = "medium"


@dataclass
class WaitIntent:
    """Intent to wait for a condition or duration.

    Attributes:
        condition: Callable that returns True when wait is complete
        timeout: Maximum time to wait in seconds
        poll_interval: Time between condition checks in seconds
        description: Human-readable description of what we're waiting for
    """

    condition: Callable[[], bool]
    timeout: float
    poll_interval: float = 0.1
    description: str = "waiting"


@dataclass
class SleepIntent:
    """Intent to sleep for a fixed duration.

    Simpler than WaitIntent when no condition checking is needed.

    Attributes:
        duration: Time to sleep in seconds
    """

    duration: float


@dataclass
class DropIntent:
    """Intent to drop inventory items.

    Attributes:
        skip_slots: List of slot indices to keep (0-27)
        skip_rows: Number of rows from top to keep (0-6)
    """

    skip_slots: List[int] = field(default_factory=list)
    skip_rows: int = 0


@dataclass
class DropSlotsIntent:
    """Intent to drop specific inventory slots.

    Attributes:
        slots: List of slot indices to drop (0-27)
    """

    slots: List[int] = field(default_factory=list)


@dataclass
class LogoutIntent:
    """Intent to logout the game client.

    Attributes:
        reason: Reason for logging out (for logging)
    """

    reason: str


@dataclass
class StopIntent:
    """Intent to stop the bot.

    Attributes:
        reason: Reason for stopping (for logging)
    """

    reason: str


@dataclass
class LogMessageIntent:
    """Intent to log a message.

    Attributes:
        message: The message to log
    """

    message: str


@dataclass
class TypeIntent:
    """Intent to type text via keyboard.

    Attributes:
        text: The text to type
        interval: Delay between keystrokes in seconds
        field_name: Optional description of which field is being typed into
        mask_in_logs: Whether to mask the text in logs (for passwords)
    """

    text: str
    interval: float = 0.05
    field_name: str = ""
    mask_in_logs: bool = False


@dataclass
class KeyPressIntent:
    """Intent to press a keyboard key.

    Attributes:
        key: The key to press (e.g., "enter", "tab", "escape")
        hold_duration: How long to hold the key in seconds (0 = tap)
    """

    key: str
    hold_duration: float = 0.0


@dataclass
class LaunchIntent:
    """Intent to launch a process and wait for its window.

    Attributes:
        command: Command to run (list of strings for subprocess)
        expected_window: Window title pattern to confirm launch succeeded
        timeout: Maximum time to wait for window to appear
        exact_match: If True, require exact window title match
    """

    command: List[str]
    expected_window: str
    timeout: float = 30.0
    exact_match: bool = False


@dataclass
class CompositeIntent:
    """Intent that combines multiple intents to be executed in sequence.

    Attributes:
        intents: List of intents to execute in order
    """

    intents: List[
        Union[
            ClickIntent,
            MoveIntent,
            WaitIntent,
            SleepIntent,
            DropIntent,
            DropSlotsIntent,
            LogoutIntent,
            StopIntent,
            LogMessageIntent,
            TypeIntent,
            KeyPressIntent,
            LaunchIntent,
        ]
    ] = field(default_factory=list)


# Type alias for any intent type
Intent = Union[
    ClickIntent,
    MoveIntent,
    WaitIntent,
    SleepIntent,
    DropIntent,
    DropSlotsIntent,
    LogoutIntent,
    StopIntent,
    LogMessageIntent,
    TypeIntent,
    KeyPressIntent,
    LaunchIntent,
    CompositeIntent,
]
