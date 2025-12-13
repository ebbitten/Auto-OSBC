#!/usr/bin/env python3
"""
Cross-platform installation script for Auto-OSBC
Supports Windows 10/11 and Ubuntu 20/22
"""
import os
import sys
import platform
import subprocess
import venv
from pathlib import Path

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

def check_python_version():
    """Ensure Python 3.10+ is available"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required. Found: {version.major}.{version.minor}")
        print("Please install Python 3.10 or newer and try again.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_virtual_environment():
    """Create and activate virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return venv_path
    
    print("🔨 Creating virtual environment...")
    try:
        venv.create(venv_path, with_pip=True)
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

def install_dependencies(venv_path, platform_name):
    """Install dependencies using setup.py"""
    pip_exe = get_pip_executable(venv_path)
    
    print("📦 Installing core dependencies...")
    
    # Install main package
    try:
        subprocess.run([str(pip_exe), "install", "-e", "."], check=True)
        print("✅ Core dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install core dependencies: {e}")
        return False
    
    # Install development dependencies if requested
    print("🔧 Installing development dependencies...")
    try:
        subprocess.run([str(pip_exe), "install", "-e", ".[dev]"], check=True)
        print("✅ Development dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not install dev dependencies: {e}")
    
    return True

def show_activation_instructions(venv_path):
    """Show how to activate the virtual environment"""
    system = platform.system()
    
    print("\n🎉 Installation complete!")
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    
    if system == "Windows":
        print(f"   {venv_path / 'Scripts' / 'activate.bat'}")
        print("   # or in PowerShell:")
        print(f"   {venv_path / 'Scripts' / 'Activate.ps1'}")
    else:
        print(f"   source {venv_path / 'bin' / 'activate'}")
    
    print("2. Run the application:")
    print("   python src/OSBC.py")
    print("\n3. To deactivate later:")
    print("   deactivate")

def main():
    """Main installation function"""
    print("🚀 Auto-OSBC Cross-Platform Installer")
    print("=" * 40)
    
    # Check platform compatibility
    platform_name, version = get_platform_info()
    print(f"🖥️  Platform: {platform_name} {version}")
    
    if platform_name not in ["windows", "ubuntu", "linux"]:
        print(f"⚠️  Warning: {platform_name} is not officially supported")
        print("Supported platforms: Windows 10/11, Ubuntu 20/22")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    if not venv_path:
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(venv_path, platform_name):
        sys.exit(1)
    
    # Show activation instructions
    show_activation_instructions(venv_path)

if __name__ == "__main__":
    main()