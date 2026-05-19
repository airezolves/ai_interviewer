#!/bin/bash
# Setup script for InterviewKit AI

set -e

echo "=== InterviewKit AI — Project Setup ==="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required. Please install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION detected"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not found. Frontend setup will be skipped."
    echo "   Install Node.js 18+ from https://nodejs.org"
else
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION detected"
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. You'll need PostgreSQL and Redis running manually."
    echo "   Install Docker from https://www.docker.com/products/docker-desktop"
else
    echo "✓ Docker detected"
fi

echo ""
echo "─── Setting up environment ───"

# Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
    echo "  ⚠️  Please edit .env and add your API keys!"
else
    echo "✓ .env already exists"
fi

# Create data directories
mkdir -p data/uploads data/outputs data/temp
touch data/uploads/.gitkeep data/outputs/.gitkeep data/temp/.gitkeep
echo "✓ Data directories created"

echo ""
echo "─── Installing Python dependencies ───"

# Install Python deps using the venv-ai at root
VENV_PATH="../../venv-ai"
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✓ Activated venv-ai"
else
    echo "⚠️  venv-ai not found at $VENV_PATH"
    echo "   Please create it: python3 -m venv ../../venv-ai"
fi

pip install -r requirements.txt
echo "✓ Python dependencies installed"

echo ""
echo "─── Setting up Frontend ───"

if command -v node &> /dev/null; then
    cd frontend
    npm install
    cd ..
    echo "✓ Frontend dependencies installed"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys (ANTHROPIC_API_KEY, etc.)"
echo "  2. Start infrastructure: docker-compose up postgres redis -d"
echo "  3. Initialize DB: psql < scripts/init_db.sql"
echo "  4. Start backend: bash scripts/start_dev.sh"
echo "  5. Start frontend: cd frontend && npm run dev"
echo "═══════════════════════════════════════════"
