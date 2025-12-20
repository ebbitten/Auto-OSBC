#!/bin/bash
# Auto-OSBC Installation Script for Ubuntu 20/22/24 with UV Package Manager
# Usage: ./install-ubuntu.sh

set -e  # Exit on any error

echo "🚀 Auto-OSBC Ubuntu Installation (UV + Python 3.10)"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Step 1: Check Ubuntu Version
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 1: Checking Ubuntu version...${NC}"
echo "======================================"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" ]]; then
        echo -e "${BLUE}🖥️  Detected: Ubuntu $VERSION_ID${NC}"
        if [[ "$VERSION_ID" == "20.04" || "$VERSION_ID" == "22.04" || "$VERSION_ID" == "24.04" ]]; then
            echo -e "${GREEN}✅ Ubuntu version supported${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: Ubuntu $VERSION_ID not officially tested${NC}"
            echo "Officially supported: Ubuntu 20.04, 22.04, 24.04"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Warning: Non-Ubuntu Linux detected: $ID${NC}"
        echo "This script is optimized for Ubuntu. Proceed with caution."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${RED}❌ Could not detect OS version${NC}"
    exit 1
fi

# ============================================================================
# Step 2: Check and Install Python 3.10
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 2: Checking Python 3.10...${NC}"
echo "===================================="

PYTHON_CMD=""
PYTHON_VERSION=""

# Check for Python 3.10 (preferred)
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    PYTHON_VERSION=$(python3.10 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    echo -e "${GREEN}✅ Python $PYTHON_VERSION found (recommended)${NC}"
# Check for Python 3.11/3.12 (acceptable)
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VERSION=$(python3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    echo -e "${YELLOW}⚠️  Python $PYTHON_VERSION found (acceptable, but 3.10 recommended)${NC}"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$(python3.12 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    echo -e "${YELLOW}⚠️  Python $PYTHON_VERSION found (acceptable, but 3.10 recommended)${NC}"
else
    echo -e "${RED}❌ Python 3.10, 3.11, or 3.12 not found${NC}"
    echo ""
    echo "Installing Python 3.10..."
    echo "Running: sudo apt update && sudo apt install -y python3.10 python3.10-venv python3.10-dev"
    echo ""

    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3.10-dev

    if command -v python3.10 &> /dev/null; then
        PYTHON_CMD="python3.10"
        PYTHON_VERSION=$(python3.10 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
        echo -e "${GREEN}✅ Python $PYTHON_VERSION installed${NC}"
    else
        echo -e "${RED}❌ Failed to install Python 3.10${NC}"
        exit 1
    fi
fi

# ============================================================================
# Step 3: Install System Dependencies
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 3: Installing system dependencies...${NC}"
echo "============================================="

echo "Installing required system packages..."
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-tk \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgobject-2.0-dev \
    libgirepository1.0-dev \
    pkg-config \
    curl

echo -e "${GREEN}✅ System dependencies installed${NC}"

# ============================================================================
# Step 4: Install UV Package Manager
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 4: Installing UV package manager...${NC}"
echo "==========================================="

UV_INSTALLED=false

# Check if UV is already installed
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1)
    echo -e "${GREEN}✅ UV already installed: $UV_VERSION${NC}"
    UV_INSTALLED=true
else
    echo "📥 UV not found, installing automatically..."
    echo "Running: curl -LsSf https://astral.sh/uv/install.sh | sh"

    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        # Add UV to PATH for this session
        export PATH="$HOME/.cargo/bin:$PATH"

        # Verify installation
        if command -v uv &> /dev/null; then
            UV_VERSION=$(uv --version 2>&1)
            echo -e "${GREEN}✅ UV installed successfully: $UV_VERSION${NC}"
            UV_INSTALLED=true
        else
            echo -e "${YELLOW}⚠️  UV installation completed but not found in PATH${NC}"
            echo "   Falling back to standard pip installation..."
        fi
    else
        echo -e "${YELLOW}⚠️  UV installation failed${NC}"
        echo "   Falling back to standard pip installation..."
    fi
fi

# ============================================================================
# Step 5: Create Virtual Environment
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 5: Creating Python 3.10 virtual environment...${NC}"
echo "======================================================"

VENV_WITH_UV=false

if [ -d "venv" ]; then
    echo "📁 Virtual environment already exists"
    read -p "Recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing venv..."
        rm -rf venv
    else
        echo "Keeping existing venv"
        VENV_WITH_UV=$UV_INSTALLED
    fi
fi

if [ ! -d "venv" ]; then
    if [ "$UV_INSTALLED" = true ]; then
        echo "🔨 Creating venv with UV (Python 3.10)..."
        if uv venv --python 3.10; then
            echo -e "${GREEN}✅ Virtual environment created with UV${NC}"
            VENV_WITH_UV=true
        else
            echo -e "${YELLOW}⚠️  UV venv creation failed, falling back...${NC}"
            echo "🔨 Creating venv with standard Python..."
            $PYTHON_CMD -m venv venv
            echo -e "${GREEN}✅ Virtual environment created${NC}"
        fi
    else
        echo "🔨 Creating venv with standard Python..."
        $PYTHON_CMD -m venv venv
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    fi
fi

# ============================================================================
# Step 6: Install Dependencies
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 6: Installing dependencies...${NC}"
echo "======================================"

# Activate virtual environment
source venv/bin/activate

INSTALLED_WITH_UV=false

if [ "$VENV_WITH_UV" = true ]; then
    echo "📦 Installing with UV (fast)..."
    if uv pip install -e ".[dev]"; then
        echo -e "${GREEN}✅ Dependencies installed with UV${NC}"
        INSTALLED_WITH_UV=true
    else
        echo -e "${YELLOW}⚠️  UV installation failed, falling back to pip...${NC}"
    fi
fi

if [ "$INSTALLED_WITH_UV" = false ]; then
    echo "📦 Installing with pip..."

    # Upgrade pip first
    pip install --upgrade pip

    # Install the package
    if pip install -e ".[dev]"; then
        echo -e "${GREEN}✅ Dependencies installed with pip${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    fi
fi

# ============================================================================
# Step 7: Verify Installation
# ============================================================================
echo ""
echo -e "${CYAN}📋 Step 7: Verifying installation...${NC}"
echo "===================================="

if python -c "import src.OSBC" 2>/dev/null; then
    echo -e "${GREEN}✅ Auto-OSBC imports successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Could not import src.OSBC${NC}"
    echo "   Installation may be incomplete"
fi

# Check core dependencies
if python -c "import numpy, cv2, PIL" 2>/dev/null; then
    echo -e "${GREEN}✅ Core dependencies verified${NC}"
else
    echo -e "${YELLOW}⚠️  Some core dependencies missing${NC}"
fi

# ============================================================================
# Installation Complete
# ============================================================================
echo ""
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo "========================"
echo ""
echo "📊 Installation Summary:"
echo "   • Platform: Ubuntu $VERSION_ID"
echo "   • Python: $PYTHON_VERSION"
if [ "$INSTALLED_WITH_UV" = true ]; then
    echo "   • UV: $UV_VERSION"
    echo "   • Package Manager: UV (10-100x faster than pip)"
else
    echo "   • Package Manager: pip (fallback)"
fi
echo "   • Environment: venv/"
echo "   • Dependencies: Installed from pyproject.toml"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo "============"
echo ""
echo "1️⃣  Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2️⃣  Run Auto-OSBC:"
echo "   python src/OSBC.py"
echo ""
echo "3️⃣  To deactivate later:"
echo "   deactivate"
echo ""

if [ "$INSTALLED_WITH_UV" = true ]; then
    echo -e "${CYAN}📦 Dependency Management (with UV):${NC}"
    echo "   Add package:     uv pip install package-name"
    echo "   Update all:      uv pip install -e \".[dev]\" --upgrade"
    echo "   List installed:  uv pip list"
    echo ""
fi

echo -e "${YELLOW}📝 Notes:${NC}"
echo "   • Your game client must be installed and configured"
echo "   • See README.md for configuration instructions"
echo "   • See CLAUDE.md for development workflow"
echo ""

# Add UV to shell profile for future sessions
if [ "$UV_INSTALLED" = true ]; then
    UV_PATH_EXPORT='export PATH="$HOME/.cargo/bin:$PATH"'

    for profile_file in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
        if [ -f "$profile_file" ]; then
            if ! grep -q ".cargo/bin" "$profile_file"; then
                echo "" >> "$profile_file"
                echo "# UV package manager" >> "$profile_file"
                echo "$UV_PATH_EXPORT" >> "$profile_file"
                echo -e "${BLUE}ℹ️  Added UV to $profile_file${NC}"
            fi
        fi
    done

    echo ""
    echo -e "${BLUE}ℹ️  UV has been added to your shell profile${NC}"
    echo "   Run 'source ~/.bashrc' or restart your terminal to use UV globally"
fi
