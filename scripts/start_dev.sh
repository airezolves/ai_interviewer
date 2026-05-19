#!/bin/bash
# Start all backend services for local development

set -e

echo "=== Starting InterviewKit AI Services ==="

# Activate virtual environment
VENV_PATH="../../venv-ai"
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

export PYTHONPATH="$(pwd)"

# Function to start a service in background
start_service() {
    local name=$1
    local module=$2
    local port=$3
    
    echo "Starting $name on port $port..."
    uvicorn "$module" --host 0.0.0.0 --port "$port" --reload &
    echo "  PID: $!"
}

# Start services
start_service "Gateway"        "services.gateway.app:app"        8000
start_service "Auth"           "services.auth.app:app"           8001
start_service "Resume Parser"  "services.resume_parser.app:app"  8002
start_service "AI Engine"      "services.ai_engine.app:app"      8003
start_service "Kit Manager"    "services.kit_manager.app:app"    8004
start_service "PDF Generator"  "services.pdf_generator.app:app"  8005
start_service "Billing"        "services.billing.app:app"        8006

echo ""
echo "═══════════════════════════════════════"
echo "All services started!"
echo ""
echo "  Gateway:        http://localhost:8000"
echo "  Auth:           http://localhost:8001"
echo "  Resume Parser:  http://localhost:8002"
echo "  AI Engine:      http://localhost:8003"
echo "  Kit Manager:    http://localhost:8004"
echo "  PDF Generator:  http://localhost:8005"
echo "  Billing:        http://localhost:8006"
echo ""
echo "  API Docs:       http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "═══════════════════════════════════════"

# Wait for all background processes
wait
