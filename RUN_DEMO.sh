#!/bin/bash

# AI Investment Scout DAO - Demo Runner
# This script helps you run the complete demo

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║         AI INVESTMENT SCOUT DAO - DEMO SETUP               ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running from project root
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📋 This script will help you run the demo in 3 steps:"
echo "   1. Check dependencies"
echo "   2. Install packages"
echo "   3. Show commands to run in separate terminals"
echo ""

# Step 1: Check dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Checking Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python installed: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js installed: $NODE_VERSION"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm installed: $NPM_VERSION"
else
    echo "❌ npm not found. Please install npm"
    exit 1
fi

echo ""
read -p "Press Enter to continue with installation..."

# Step 2: Install packages
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Installing Packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Setup Python virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Install Python packages
echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Python packages installed"

# Install Node packages
echo "📦 Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..
echo "✅ Frontend packages installed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Running the Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Installation complete! Now you need to run 3 commands in separate terminals:"
echo ""
echo "┌────────────────────────────────────────────────────────────┐"
echo "│ TERMINAL 1: Backend                                        │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""
echo "cd $(pwd)/backend"
echo "source $(pwd)/.venv/bin/activate"
echo "uvicorn app.main:app --reload"
echo ""
echo "┌────────────────────────────────────────────────────────────┐"
echo "│ TERMINAL 2: Frontend                                       │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""
echo "cd $(pwd)/frontend"
echo "npm run dev"
echo ""
echo "┌────────────────────────────────────────────────────────────┐"
echo "│ TERMINAL 3: SpoonOS Agent (Demo)                          │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""
echo "source $(pwd)/.venv/bin/activate"
echo "python $(pwd)/spoon_agent/main.py --demo"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 URLs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "README.md          - Complete documentation"
echo "QUICKSTART.md      - Quick start guide"
echo "PROJECT_SUMMARY.md - Project overview"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Setup complete! Open the URLs above in your browser after"
echo "   starting all three terminals."
echo ""
echo "💡 TIP: You can also run these commands manually. See QUICKSTART.md"
echo ""

