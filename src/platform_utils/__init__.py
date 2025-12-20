"""
Platform utilities for Auto-OSBC
Centralized platform detection, path handling, compatibility checks, and process management
"""

# Detection functions
from .detection import (
    get_platform,
    get_windows_version,
    get_ubuntu_version,
    detect_wsl2,
    get_detailed_platform_info,
    PlatformType,
    WindowsVersion,
    UbuntuVersion,
)

# Path utilities
from .paths import (
    get_python_executable_name,
    get_venv_activation_command,
    get_pip_executable_path,
)

# Compatibility functions
from .compatibility import (
    check_python_version,
    is_platform_supported,
    get_platform_specific_dependencies,
    get_wsl2_compatibility_warnings,
    show_platform_info,
)

# Process management
from .process import (
    terminate_thread,
    launch_detached_process,
)

__all__ = [
    # Detection
    "get_platform",
    "get_windows_version",
    "get_ubuntu_version",
    "detect_wsl2",
    "get_detailed_platform_info",
    "PlatformType",
    "WindowsVersion",
    "UbuntuVersion",
    # Paths
    "get_python_executable_name",
    "get_venv_activation_command",
    "get_pip_executable_path",
    # Compatibility
    "check_python_version",
    "is_platform_supported",
    "get_platform_specific_dependencies",
    "get_wsl2_compatibility_warnings",
    "show_platform_info",
    # Process
    "terminate_thread",
    "launch_detached_process",
]
