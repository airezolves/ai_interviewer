#!/bin/bash
# Run all backend services in parallel (local dev without Docker)
set -e

trap 'kill 0' EXIT

echo "Starting InterviewKit AI services..."
echo "─────────────────────────────────────"

cd "$(dirname "$0")/.."

# Start each service in background
uvicorn backend.gateway.app.main:app --host 0.0.0.0 --port 8000 --reload &
echo "✓ Gateway      → http://localhost:8000"

uvicorn backend.auth.app.main:app --host 0.0.0.0 --port 8001 --reload &
echo "✓ Auth         → http://localhost:8001"

uvicorn backend.resume.app.main:app --host 0.0.0.0 --port 8002 --reload &
echo "✓ Resume       → http://localhost:8002"

uvicorn backend.ai_engine.app.main:app --host 0.0.0.0 --port 8003 --reload &
echo "✓ AI Engine    → http://localhost:8003"

uvicorn backend.kit_orchestrator.app.main:app --host 0.0.0.0 --port 8004 --reload &
echo "✓ Orchestrator → http://localhost:8004"

uvicorn backend.export.app.main:app --host 0.0.0.0 --port 8005 --reload &
echo "✓ Export       → http://localhost:8005"

echo ""
echo "─────────────────────────────────────"
echo "All services running. Press Ctrl+C to stop all."
wait
