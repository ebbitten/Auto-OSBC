#!/usr/bin/env python3
"""
Cross-platform installation script for Auto-OSBC with UV support
Supports Windows 10/11 and Ubuntu 20/22/24
Automatically installs UV package manager and prefers Python 3.10
"""
import os
import sys
import platform
import subprocess
import shutil
import venv
from pathlib import Path

# Fix Windows terminal encoding for emoji support
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_platform_info():
    """Get detailed platform information"""
    system = platform.system()
    release = platform.release()

    if system == "Windows":
        version = platform.version()
        # Check if Windows 10/11
        if "10.0" in version:
            return "windows", "10+"
    elif system == "Linux":
        # Check for Ubuntu
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read()
                if "ubuntu" in content.lower():
                    # Extract Ubuntu version
                    for line in content.split("\n"):
                        if line.startswith("VERSION_ID="):
                            version = line.split('"')[1]
                            return "ubuntu", version
        except FileNotFoundError:
            pass

    return system.lower(), release


def find_python_310():
    """
    Find Python 3.10 executable, or acceptable alternative (3.11, 3.12)
    Returns tuple: (executable_path, version_string, is_preferred)
    """
    system = platform.system()
    candidates = []

    # Windows: Try py launcher first
    if system == "Windows":
        for version in ["3.10", "3.11", "3.12"]:
            try:
                result = subprocess.run(
                    ["py", f"-{version}", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_str = result.stdout.strip().split()[1]
                    is_preferred = version == "3.10"
                    candidates.append((f"py -{version}", version_str, is_preferred))
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    # Unix: Try python3.10, python3.11, python3.12
    else:
        for version in ["3.10", "3.11", "3.12"]:
            exe_name = f"python{version}"
            if shutil.which(exe_name):
                try:
                    result = subprocess.run(
                        [exe_name, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        version_str = result.stdout.strip().split()[1]
                        is_preferred = version == "3.10"
                        candidates.append((exe_name, version_str, is_preferred))
                except subprocess.TimeoutExpired:
                    pass

    # Also check current Python
    current_version = sys.version_info
    if 10 <= current_version.minor <= 12 and current_version.major == 3:
        version_str = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
        is_preferred = current_version.minor == 10
        candidates.append((sys.executable, version_str, is_preferred))

    # Sort by preference (preferred first, then by version)
    candidates.sort(key=lambda x: (not x[2], x[1]), reverse=True)

    return candidates[0] if candidates else (None, None, False)


def check_python_version():
    """Ensure Python 3.10-3.12 is available"""
    python_exe, version_str, is_preferred = find_python_310()

    if not python_exe:
        print("❌ Python 3.10, 3.11, or 3.12 required")
        print("   Please install Python 3.10 (recommended) from:")
        print("   https://www.python.org/downloads/release/python-31011/")
        return None, None

    status = "✅" if is_preferred else "⚠️"
    pref_text = "(recommended)" if is_preferred else "(acceptable, but 3.10 recommended)"
    print(f"{status} Python {version_str} detected {pref_text}")

    return python_exe, version_str


def install_uv():
    """
    Install UV package manager if not already installed
    Returns True if UV is available after installation
    """
    # Check if UV is already installed
    if shutil.which("uv"):
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ UV already installed: {result.stdout.strip()}")
                return True
        except subprocess.TimeoutExpired:
            pass

    print("📥 UV not found, installing automatically...")

    system = platform.system()

    try:
        if system == "Windows":
            # Windows: Use PowerShell installer
            print("   Running: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "ByPass", "-Command",
                 "irm https://astral.sh/uv/install.ps1 | iex"],
                timeout=120
            )

            if result.returncode != 0:
                print("⚠️  PowerShell installation failed, trying manual method...")
                return False

            # Add to PATH for this session
            uv_path = Path.home() / ".cargo" / "bin"
            if uv_path.exists():
                os.environ["PATH"] = f"{uv_path}{os.pathsep}{os.environ['PATH']}"

        else:
            # Linux/macOS: Use curl installer
            print("   Running: curl -LsSf https://astral.sh/uv/install.sh | sh")
            result = subprocess.run(
                ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
                timeout=120
            )

            if result.returncode != 0:
                print("⚠️  Curl installation failed")
                return False

            # Add to PATH for this session
            uv_path = Path.home() / ".cargo" / "bin"
            if uv_path.exists():
                os.environ["PATH"] = f"{uv_path}{os.pathsep}{os.environ['PATH']}"

        # Verify installation
        if shutil.which("uv"):
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ UV installed successfully: {result.stdout.strip()}")
                return True

        print("⚠️  UV installation completed but not found in PATH")
        return False

    except subprocess.TimeoutExpired:
        print("⚠️  UV installation timed out")
        return False
    except Exception as e:
        print(f"⚠️  UV installation failed: {e}")
        return False


def create_virtual_environment_uv(python_exe):
    """Create virtual environment using UV (preferred)"""
    venv_path = Path("venv")

    if venv_path.exists():
        print("📁 Virtual environment already exists")
        response = input("   Recreate it? (y/N): ")
        if response.lower() == 'y':
            print("🗑️  Removing existing venv...")
            shutil.rmtree(venv_path)
        else:
            return venv_path

    print("🔨 Creating virtual environment with UV (Python 3.10)...")
    try:
        # Try to create with UV specifying Python 3.10
        # UV defaults to .venv, so specify venv explicitly
        result = subprocess.run(
            ["uv", "venv", "venv", "--python", "3.10"],
            timeout=60
        )

        if result.returncode == 0:
            print("✅ Virtual environment created with UV")
            return venv_path
        else:
            print("⚠️  UV venv creation failed, trying fallback...")
            return None

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️  UV venv failed: {e}")
        return None


def create_virtual_environment_standard(python_exe):
    """Create virtual environment using standard venv (fallback)"""
    venv_path = Path("venv")

    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return venv_path

    print("🔨 Creating virtual environment with standard venv...")
    try:
        # Handle py launcher format
        if python_exe.startswith("py -"):
            exe_parts = python_exe.split()
            subprocess.run([*exe_parts, "-m", "venv", "venv"], check=True, timeout=60)
        else:
            subprocess.run([python_exe, "-m", "venv", "venv"], check=True, timeout=60)

        print("✅ Virtual environment created")
        return venv_path

    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return None


def get_pip_executable(venv_path):
    """Get pip executable path for the virtual environment"""
    system = platform.system()
    if system == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def install_dependencies_uv(venv_path):
    """Install dependencies using UV (preferred)"""
    print("📦 Installing dependencies with UV (fast)...")

    try:
        # Use uv pip with explicit python path to target the venv
        system = platform.system()
        if system == "Windows":
            python_exe = str(venv_path / "Scripts" / "python.exe")
        else:
            python_exe = str(venv_path / "bin" / "python")

        result = subprocess.run(
            ["uv", "pip", "install", "--python", python_exe, "-e", ".[dev]"],
            timeout=300
        )

        if result.returncode == 0:
            print("✅ Dependencies installed with UV")
            return True
        else:
            print("⚠️  UV installation failed, falling back to pip...")
            return False

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️  UV install failed: {e}")
        return False


def install_dependencies_pip(venv_path):
    """Install dependencies using standard pip (fallback)"""
    pip_exe = get_pip_executable(venv_path)

    print("📦 Installing dependencies with pip...")

    # Upgrade pip first
    try:
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], timeout=60)
    except subprocess.TimeoutExpired:
        print("⚠️  Pip upgrade timed out, continuing...")

    # Install main package with dev dependencies
    try:
        subprocess.run([str(pip_exe), "install", "-e", ".[dev]"], check=True, timeout=300)
        print("✅ Dependencies installed with pip")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False


def show_activation_instructions(venv_path, used_uv):
    """Show how to activate the virtual environment and use the project"""
    system = platform.system()

    print("\n" + "=" * 60)
    print("🎉 Installation Complete!")
    print("=" * 60)

    if used_uv:
        print("📦 Package Manager: UV (10-100x faster than pip)")
    else:
        print("📦 Package Manager: pip (fallback)")

    print("\n📋 Next Steps:")
    print("=" * 60)

    print("\n1️⃣  Activate the virtual environment:")
    if system == "Windows":
        print(f"   {venv_path / 'Scripts' / 'activate.bat'}")
        print("   # or in PowerShell:")
        print(f"   {venv_path / 'Scripts' / 'Activate.ps1'}")
    else:
        print(f"   source {venv_path / 'bin' / 'activate'}")

    print("\n2️⃣  Run Auto-OSBC:")
    print("   python src/OSBC.py")

    print("\n3️⃣  To deactivate later:")
    print("   deactivate")

    if used_uv:
        print("\n📦 Dependency Management with UV:")
        print("   Add package:     uv pip install package-name")
        print("   Update all:      uv pip install -e \".[dev]\" --upgrade")
        print("   List installed:  uv pip list")

    print("\n📝 Notes:")
    print("   • See README.md for configuration instructions")
    print("   • See CLAUDE.md for development workflow")
    print("   • Ensure your game client is installed")
    print()


def main():
    """Main installation function"""
    print("🚀 Auto-OSBC Cross-Platform Installer (UV + Python 3.10)")
    print("=" * 60)

    # Check platform compatibility
    platform_name, version = get_platform_info()
    print(f"🖥️  Platform: {platform_name} {version}")

    if platform_name not in ["windows", "ubuntu", "linux"]:
        print(f"⚠️  Warning: {platform_name} is not officially supported")
        print("   Supported platforms: Windows 10/11, Ubuntu 20.04/22.04/24.04")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Check Python version
    python_exe, python_version = check_python_version()
    if not python_exe:
        sys.exit(1)

    # Try to install UV
    print()
    uv_available = install_uv()

    # Create virtual environment
    print()
    venv_path = None
    used_uv = False

    if uv_available:
        venv_path = create_virtual_environment_uv(python_exe)
        used_uv = venv_path is not None

    if not venv_path:
        print("📋 Falling back to standard venv...")
        venv_path = create_virtual_environment_standard(python_exe)

    if not venv_path:
        print("❌ Failed to create virtual environment")
        sys.exit(1)

    # Install dependencies
    print()
    install_success = False

    if used_uv:
        install_success = install_dependencies_uv(venv_path)

    if not install_success:
        if used_uv:
            print("📋 Falling back to pip...")
        install_success = install_dependencies_pip(venv_path)
        used_uv = False

    if not install_success:
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Show activation instructions
    show_activation_instructions(venv_path, used_uv)


if __name__ == "__main__":
    main()
