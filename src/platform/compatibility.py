"""
Platform compatibility and version checking for Auto-OSBC
Validates Python versions, platform support, and WSL2 compatibility
"""
import sys
from typing import Tuple
from .detection import get_platform, get_windows_version, get_ubuntu_version, detect_wsl2


def check_python_version() -> Tuple[bool, str]:
    """
    Check if the current Python version meets requirements (3.10+).

    Returns:
        Tuple of (is_compatible, version_string)
    """
    version = sys.version_info
    version_string = f"{version[0]}.{version[1]}.{version[2]}"
    is_compatible = version[0] >= 3 and version[1] >= 10

    return is_compatible, version_string


def is_platform_supported() -> bool:
    """
    Check if the current platform is officially supported.

    Returns:
        True if platform is supported (Windows 10/11 or Ubuntu 20/22)
    """
    platform_type = get_platform()

    if platform_type == "windows":
        windows_version = get_windows_version()
        return windows_version in ["10", "11"]
    elif platform_type == "linux":
        ubuntu_version = get_ubuntu_version()
        return ubuntu_version in ["20.04", "22.04", "24.04"]

    return False


def get_platform_specific_dependencies() -> dict:
    """
    Get platform-specific dependencies that might be needed.

    Returns:
        Dictionary of platform-specific packages
    """
    platform_type = get_platform()

    dependencies = {
        "windows": [
            # Windows-specific packages if needed
        ],
        "linux": [
            # Linux-specific packages if needed
            # "evdev",  # Currently not used
        ],
        "darwin": [
            # macOS-specific packages if needed
        ]
    }

    return dependencies.get(platform_type, [])


def get_wsl2_compatibility_warnings() -> list:
    """
    Get WSL2 compatibility warnings and limitations.

    Returns:
        List of warning messages for WSL2 users
    """
    if not detect_wsl2():
        return []

    warnings = [
        "WSL2 Environment Detected - GUI Functionality Limited:",
        "• Window detection (PyWinCtl) may not access Windows host windows",
        "• Screenshot capture (MSS) may fail or capture WSL desktop only",
        "• Mouse automation (PyAutoGUI) may not work cross-boundary",
        "• Game clients should run on Windows host, not WSL2 guest",
        "",
        "Recommendations:",
        "• Use native Windows installation for full functionality",
        "• Or use native Ubuntu installation instead of WSL2",
        "• For development: WSL2 is OK for code editing and non-GUI testing"
    ]

    return warnings


def show_platform_info() -> None:
    """Print detailed platform information for debugging."""
    from .detection import get_detailed_platform_info

    platform_type, details = get_detailed_platform_info()
    python_compatible, python_version = check_python_version()
    supported = is_platform_supported()
    is_wsl2 = detect_wsl2()

    print(f"Platform: {details}")
    print(f"Python: {python_version} {'✅' if python_compatible else '❌'}")
    print(f"Supported: {'✅' if supported else '⚠️'}")

    if is_wsl2:
        print("WSL2: ⚠️  Detected (GUI limitations expected)")

    if not supported:
        print("Note: Officially supported platforms are Windows 10/11 and Ubuntu 20.04/22.04/24.04")

    # Show WSL2 warnings if detected
    wsl2_warnings = get_wsl2_compatibility_warnings()
    if wsl2_warnings:
        print()
        for warning in wsl2_warnings:
            print(warning)
