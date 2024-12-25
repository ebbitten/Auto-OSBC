from typing import Any, Callable, TypeVar, cast
from functools import wraps
import sys

T = TypeVar('T')

def check_attributes(module: Any, required_attrs: list[str]) -> None:
    """
    Check if a module has all required attributes.
    
    Args:
        module: The module to check
        required_attrs: List of attribute names that should exist
        
    Raises:
        AttributeError: If any required attribute is missing
    """
    missing_attrs = []
    for attr in required_attrs:
        if not hasattr(module, attr):
            missing_attrs.append(attr)
    
    if missing_attrs:
        raise AttributeError(
            f"Module {module.__name__} missing required attributes: {', '.join(missing_attrs)}"
        )

def validate_module_attributes(*required_attrs: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to validate that required module attributes exist before calling a function.
    
    Args:
        *required_attrs: Names of attributes that should exist on imported modules
        
    Returns:
        Decorator function that checks module attributes
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Check each module referenced in the required attributes
            for attr in required_attrs:
                if '.' in attr:
                    module_name, attr_name = attr.split('.', 1)
                    # Get module from sys.modules if it's imported
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        check_attributes(module, [attr_name])
                    else:
                        raise ImportError(f"Module {module_name} not imported")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 