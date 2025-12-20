"""
Platform-specific path utilities for Auto-OSBC
Handles virtual environment paths, executables, and platform-specific file locations
"""
from pathlib import Path
from .detection import get_platform


def get_python_executable_name() -> str:
    """
    Get the appropriate Python executable name for the current platform.

    Returns:
        Python executable name (e.g., "python", "python3")
    """
    if get_platform() == "windows":
        return "python"
    else:
        return "python3"


def get_venv_activation_command(venv_path: Path) -> str:
    """
    Get the virtual environment activation command for the current platform.

    Args:
        venv_path: Path to the virtual environment directory

    Returns:
        Command to activate the virtual environment
    """
    if get_platform() == "windows":
        return str(venv_path / "Scripts" / "activate.bat")
    else:
        return f"source {venv_path / 'bin' / 'activate'}"


def get_pip_executable_path(venv_path: Path) -> Path:
    """
    Get the pip executable path for the virtual environment.

    Args:
        venv_path: Path to the virtual environment directory

    Returns:
        Path to pip executable
    """
    if get_platform() == "windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"
