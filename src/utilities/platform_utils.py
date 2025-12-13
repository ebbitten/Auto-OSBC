"""
Cross-platform utility functions for Auto-OSBC
Provides centralized platform detection and OS-specific functionality
"""
import platform
import sys
from typing import Tuple, Literal, Optional
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


if __name__ == "__main__":
    # Show platform info when run directly
    show_platform_info()