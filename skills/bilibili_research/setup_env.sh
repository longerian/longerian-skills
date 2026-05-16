#!/bin/bash
# Bilibili Research Skill - Runtime Environment Setup
# This script creates a Python virtual environment for the skill runtime.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Skill virtual environment location
SKILL_VENV="$HOME/.longerian/venv/bilibili-research"

# Find project root (where requirements.txt lives)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"

echo "🔧 Setting up Bilibili Research skill runtime environment..."
echo "   Project root: $PROJECT_ROOT"
echo ""

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 not found. Please install Python 3.10 or later.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$SKILL_VENV" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment at: $SKILL_VENV${NC}"
    python3 -m venv "$SKILL_VENV"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists at: $SKILL_VENV${NC}"
fi

# Activate and install dependencies
echo ""
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
source "$SKILL_VENV/bin/activate"

if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -q --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found at: $REQUIREMENTS_FILE${NC}"
    exit 1
fi

deactivate

# Setup instructions
echo ""
echo -e "${GREEN}✨ Setup complete!${NC}"
echo ""
echo "To use this skill's Python environment, activate it with:"
echo ""
echo -e "  ${YELLOW}source $SKILL_VENV/bin/activate${NC}"
echo ""
echo "Or run commands directly:"
echo ""
echo -e "  ${YELLOW}$SKILL_VENV/bin/python3 <script>${NC}"
echo ""
