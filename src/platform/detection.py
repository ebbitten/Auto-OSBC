"""
Platform detection functions for Auto-OSBC
Provides centralized platform type and version detection
"""
import platform
from typing import Tuple, Literal
from pathlib import Path

# Type definitions for supported platforms
PlatformType = Literal["windows", "linux", "darwin", "unknown"]
WindowsVersion = Literal["10", "11", "unknown"]
UbuntuVersion = Literal["20.04", "22.04", "24.04", "unknown"]


def get_platform() -> PlatformType:
    """
    Get the current platform type.

    Returns:
        Platform type: windows, linux, darwin, or unknown
    """
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    elif system == "darwin":
        return "darwin"
    else:
        return "unknown"


def get_windows_version() -> WindowsVersion:
    """
    Get Windows version (10 or 11).
    Only works on Windows systems.

    Returns:
        Windows version or "unknown"
    """
    if get_platform() != "windows":
        return "unknown"

    try:
        version = platform.version()
        release = platform.release()

        # Windows 11 detection (build 22000+)
        if "10.0.22" in version or release == "11":
            return "11"
        elif "10.0" in version or release == "10":
            return "10"

    except Exception:
        pass

    return "unknown"


def get_ubuntu_version() -> UbuntuVersion:
    """
    Get Ubuntu version (20.04 or 22.04).
    Only works on Ubuntu systems.

    Returns:
        Ubuntu version or "unknown"
    """
    if get_platform() != "linux":
        return "unknown"

    try:
        os_release_path = Path("/etc/os-release")
        if os_release_path.exists():
            content = os_release_path.read_text()

            if "ubuntu" not in content.lower():
                return "unknown"

            # Extract version from VERSION_ID line
            for line in content.split("\n"):
                if line.startswith("VERSION_ID="):
                    version = line.split('"')[1] if '"' in line else line.split("=")[1]
                    if version in ["20.04", "22.04", "24.04"]:
                        return version  # type: ignore

    except Exception:
        pass

    return "unknown"


def detect_wsl2() -> bool:
    """
    Detect if running in WSL2 environment.

    Returns:
        True if running in WSL2, False otherwise
    """
    if get_platform() != "linux":
        return False

    import os

    # Method 1: Check /proc/version for Microsoft/WSL
    try:
        with open('/proc/version', 'r') as f:
            proc_version = f.read().lower()
            if 'microsoft' in proc_version or 'wsl' in proc_version:
                return True
    except (FileNotFoundError, PermissionError):
        pass

    # Method 2: Check WSL environment variables
    wsl_env_vars = ['WSL_DISTRO_NAME', 'WSL_INTEROP', 'WSLENV']
    for var in wsl_env_vars:
        if os.getenv(var):
            return True

    # Method 3: Check for WSL-specific files
    wsl_files = ['/proc/sys/fs/binfmt_misc/WSLInterop']
    for wsl_file in wsl_files:
        if Path(wsl_file).exists():
            return True

    return False


def get_detailed_platform_info() -> Tuple[PlatformType, str]:
    """
    Get detailed platform information.

    Returns:
        Tuple of (platform_type, version_info)
    """
    platform_type = get_platform()

    if platform_type == "windows":
        version = get_windows_version()
        return platform_type, f"Windows {version}"
    elif platform_type == "linux":
        ubuntu_version = get_ubuntu_version()
        if ubuntu_version != "unknown":
            wsl_suffix = " (WSL2)" if detect_wsl2() else ""
            return platform_type, f"Ubuntu {ubuntu_version}{wsl_suffix}"
        else:
            # Generic Linux info
            try:
                distro = platform.freedesktop_os_release().get("NAME", "Linux")
                wsl_suffix = " (WSL2)" if detect_wsl2() else ""
                return platform_type, f"{distro}{wsl_suffix}"
            except Exception:
                wsl_suffix = " (WSL2)" if detect_wsl2() else ""
                return platform_type, f"Linux{wsl_suffix}"
    elif platform_type == "darwin":
        mac_version = platform.mac_ver()[0]
        return platform_type, f"macOS {mac_version}"
    else:
        return platform_type, platform.system()
