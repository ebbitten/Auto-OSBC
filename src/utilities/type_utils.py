from typing import Any, Callable, TypeVar, cast
from functools import wraps
import inspect

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
            # Get all imported modules in the function's global scope
            globals_dict = inspect.getcurrentframe().f_back.f_globals  # type: ignore
            
            # Check each module referenced in the function
            source = inspect.getsource(func)
            for line in source.split('\n'):
                # Look for module usage patterns
                for attr in required_attrs:
                    if '.' in attr:
                        module_name, attr_name = attr.split('.', 1)
                        if module_name in globals_dict:
                            module = globals_dict[module_name]
                            check_attributes(module, [attr_name])
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 