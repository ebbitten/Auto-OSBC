#!/bin/bash
# Auto-OSBC Installation Script for Ubuntu 20/22
# Usage: ./install-ubuntu.sh

set -e  # Exit on any error

echo "🚀 Auto-OSBC Ubuntu Installation"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" ]]; then
        echo -e "${BLUE}🖥️  Detected: Ubuntu $VERSION_ID${NC}"
        if [[ "$VERSION_ID" == "20.04" || "$VERSION_ID" == "22.04" ]]; then
            echo -e "${GREEN}✅ Ubuntu version supported${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: Ubuntu $VERSION_ID not officially tested${NC}"
            echo "Officially supported: Ubuntu 20.04, 22.04"
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

# Check Python 3.10+
echo "🐍 Checking Python version..."
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo -e "${GREEN}✅ Python 3.10 found${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}✅ Python 3.11 found${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        PYTHON_CMD="python3"
        echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}❌ Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
        echo "Install Python 3.10+:"
        echo "  sudo apt update"
        echo "  sudo apt install python3.10 python3.10-venv python3.10-dev"
        exit 1
    fi
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Install Python 3.10+:"
    echo "  sudo apt update"
    echo "  sudo apt install python3.10 python3.10-venv python3.10-dev"
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
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
    pkg-config

echo -e "${GREEN}✅ System dependencies installed${NC}"

# Create virtual environment
echo "🔨 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "📁 Virtual environment already exists"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Auto-OSBC dependencies..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install the package
pip install -e .

# Install development dependencies
pip install -e .[dev]

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Verify installation
echo "🔍 Verifying installation..."
if python -c "import src.OSBC" 2>/dev/null; then
    echo -e "${GREEN}✅ Installation verified${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify installation${NC}"
fi

# Show completion message
echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run Auto-OSBC:"
echo "   python src/OSBC.py"
echo ""
echo "3. To deactivate later:"
echo "   deactivate"
echo ""
echo -e "${YELLOW}📝 Note: Make sure your game client is installed and configured${NC}"