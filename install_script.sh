#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo -e "${RED}ERROR: Command \"${last_command}\" failed with exit code $?.${NC}"' ERR

echo_step() {
    echo -e "${YELLOW}Step: $1${NC}"
}

# Function to check if a command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success: $1${NC}"
    else
        echo -e "${RED}✗ Failed: $1${NC}"
        exit 1
    fi
}

# Function to install a Python package
install_package() {
    local package=$1
    echo -e "${YELLOW}Installing $package...${NC}"
    $VENV_PYTHON -m pip install --no-cache-dir "$package" || {
        echo -e "${RED}Failed to install $package${NC}"
        echo -e "${YELLOW}Trying with --break-system-packages...${NC}"
        $VENV_PYTHON -m pip install --no-cache-dir --break-system-packages "$package" || {
            echo -e "${RED}Failed to install $package even with --break-system-packages${NC}"
            return 1
        }
    }
    return 0
}

echo_step "Unsetting Cursor-related variables that can interfere with installation"
unset GSETTINGS_SCHEMA_DIR APPDIR LD_LIBRARY_PATH APPIMAGE CHROME_DESKTOP

echo_step "Installing system dependencies (this may take a while)"
sudo apt-get update
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-tk \
    python3-dev \
    python3-xlib \
    python3-setuptools \
    python3-full \
    pipx \
    build-essential \
    libx11-dev \
    libxcb1-dev \
    scrot \
    xsel \
    xclip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libtiff5-dev \
    libjpeg8-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb-xinerama0-dev \
    libxcb-randr0-dev \
    libxcb-xtest0-dev \
    libxcb-shape0-dev \
    libxcb-xkb-dev
check_success "System dependencies installed"

echo_step "Removing existing virtual environment if it exists"
rm -rf .venv

echo_step "Creating new virtual environment with Python 3.10"
python3.10 -m venv .venv
check_success "Virtual environment created"

echo_step "Activating virtual environment"
source .venv/bin/activate
VENV_PYTHON=$(which python)
check_success "Virtual environment activated using Python at: $VENV_PYTHON"

echo_step "Installing pip in virtual environment"
curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
$VENV_PYTHON get-pip.py --no-warn-script-location
rm get-pip.py
check_success "Pip installed"

echo_step "Installing build tools"
$VENV_PYTHON -m pip install --upgrade pip setuptools wheel build
check_success "Build tools installed"

echo_step "Installing ewmh (required for pywinctl)"
$VENV_PYTHON -m pip install ewmh==0.1.6
check_success "ewmh installed"

echo_step "Installing core dependencies (this may take a while)"
# Install packages one by one to better handle failures
packages=(
    "customtkinter==5.1.3"
    "Pillow==9.3.0"
    "tkinter-tooltip==2.1.0"
    "opencv-python-headless==4.5.4.60"
    "numpy==1.23.1"
    "deprecated==1.2.13"
    "simplejson==3.17.6"
    "pywinctl==0.0.42"
    "mss==7.0.1"
    "pyclick==0.0.2"
    "PyTweening==1.0.4"
    "mouseinfo==0.1.3"
    "pygetwindow==0.0.9"
    "pyscreeze==0.1.28"
    "pymsgbox==1.0.9"
    "pyperclip==1.8.2"
    "PyAutoGUI==0.9.53"
)

for package in "${packages[@]}"; do
    install_package "$package"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install package: $package${NC}"
        exit 1
    fi
done
check_success "All core dependencies installed"

echo_step "Installing PyAutoGUI and dependencies in specific order"
$VENV_PYTHON -m pip uninstall -y pyautogui mouseinfo pygetwindow pymsgbox pyperclip pyscreeze pytweening python3-xlib python-xlib

packages=(
    "python-xlib==0.33"
    "python3-xlib==0.15"
    "pyperclip==1.8.2"
    "pymsgbox==1.0.9"
    "PyTweening==1.0.4"
    "mouseinfo==0.1.3"
    "pygetwindow==0.0.9"
    "pyscreeze==0.1.28"
)

# Install dependencies first
for package in "${packages[@]}"; do
    echo_step "Installing $package"
    $VENV_PYTHON -m pip install --no-cache-dir "$package"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install package: $package${NC}"
        exit 1
    fi
done

# Install PyAutoGUI without dependencies
echo_step "Installing PyAutoGUI without dependencies"
$VENV_PYTHON -m pip install --no-cache-dir --no-deps PyAutoGUI==0.9.53

# Verify the installation
echo_step "Verifying PyAutoGUI installation"
$VENV_PYTHON -c "
import pyautogui
print('PyAutoGUI version:', pyautogui.__version__)
print('PyAutoGUI location:', pyautogui.__file__)
"
check_success "PyAutoGUI verification"

echo_step "Cleaning up"
cd - > /dev/null
rm -rf /tmp/pip_install
check_success "Cleanup completed"

echo_step "Verifying installation"
echo "Python location: $($VENV_PYTHON -c 'import sys; print(sys.executable)')"
echo "Pip location: $(which pip)"

echo -e "\n${GREEN}Setup complete! To use the environment:${NC}"
echo -e "1. Run: ${YELLOW}source .venv/bin/activate${NC}"
echo -e "2. Run: ${YELLOW}python3 src/OSBC.py${NC}"
echo -e "\n${YELLOW}Note: If you encounter any issues, try running the script with --break-system-packages${NC}"

# Verify core packages were installed
echo_step "Verifying core packages"
$VENV_PYTHON -c "import customtkinter; print('customtkinter imported successfully')"
check_success "Core packages verification"
