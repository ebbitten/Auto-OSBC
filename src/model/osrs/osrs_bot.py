from abc import ABCMeta
from typing import TypeVar, Callable, Any
from functools import wraps

from model.runelite_bot import RuneLiteBot, RuneLiteWindow

T = TypeVar('T')

def validate_types(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate function argument and return types.
    For use with OSRS bot methods.
    
    Args:
        func (Callable[..., T]): Function to validate
        
    Returns:
        Callable[..., T]: Wrapped function with type validation
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        result = func(*args, **kwargs)
        return_type = func.__annotations__.get('return')
        if return_type and not isinstance(result, return_type):
            raise TypeError(f"Expected return type {return_type}, got {type(result)}")
        return result
    return wrapper

class OSRSBot(RuneLiteBot, metaclass=ABCMeta):
    win: RuneLiteWindow = None

    def __init__(self, bot_title, description) -> None:
        window = RuneLiteWindow("RuneLite")
        super().__init__("OSRS", bot_title, description, window)
