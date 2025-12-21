"""Game state abstraction layer for bot testing and live game interaction."""

from .interface import GameState
from .mock import MockGameState

__all__ = ["GameState", "MockGameState"]
