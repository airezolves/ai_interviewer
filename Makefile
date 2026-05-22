.PHONY: help setup run stop test lint migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup (install deps, create DB)
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Creating data directories..."
	mkdir -p data/uploads data/exports data/temp
	@echo "Setup complete! Run 'make run' to start services."

run: ## Start all services locally (without Docker)
	@bash scripts/run_all.sh

run-docker: ## Start all services with Docker Compose
	docker-compose up --build

stop: ## Stop Docker services
	docker-compose down

test: ## Run all tests
	pytest tests/ -v --cov=shared --cov=backend

lint: ## Run linter
	ruff check shared/ backend/ --fix
	ruff format shared/ backend/

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Reset database (WARNING: destroys all data)
	alembic downgrade base
	alembic upgrade head

gateway: ## Run gateway service only
	uvicorn backend.gateway.app.main:app --host 0.0.0.0 --port 8000 --reload

auth: ## Run auth service only
	uvicorn backend.auth.app.main:app --host 0.0.0.0 --port 8001 --reload

resume: ## Run resume service only
	uvicorn backend.resume.app.main:app --host 0.0.0.0 --port 8002 --reload

ai-engine: ## Run AI engine service only
	uvicorn backend.ai_engine.app.main:app --host 0.0.0.0 --port 8003 --reload

orchestrator: ## Run kit orchestrator service only
	uvicorn backend.kit_orchestrator.app.main:app --host 0.0.0.0 --port 8004 --reload

export: ## Run export service only
	uvicorn backend.export.app.main:app --host 0.0.0.0 --port 8005 --reload
