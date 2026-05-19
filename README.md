# InterviewKit AI

AI-powered interview preparation platform that generates complete, personalized interview kits from Job Descriptions + Resumes.

## Architecture

Microservices-based architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js + React)                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                     API Gateway (:8000)                       │
└──┬──────┬──────────┬──────────┬──────────┬──────────┬───────┘
   │      │          │          │          │          │
┌──▼─┐ ┌──▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼────┐ ┌───▼────┐
│Auth│ │Resume│ │AI      │ │Kit    │ │PDF     │ │Billing │
│:01 │ │Parser│ │Engine  │ │Manager│ │Gen     │ │:06     │
│    │ │:02   │ │:03     │ │:04    │ │:05     │ │        │
└────┘ └──────┘ └────────┘ └───────┘ └────────┘ └────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for PostgreSQL + Redis)
- Anthropic API key (for Claude)

### Setup

```bash
# 1. Clone and navigate
cd ai_interviewer

# 2. Run setup script
chmod +x scripts/setup.sh && bash scripts/setup.sh

# 3. Edit .env with your API keys
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY at minimum

# 4. Start infrastructure (PostgreSQL + Redis)
docker-compose up postgres redis -d

# 5. Initialize database
docker-compose exec postgres psql -U postgres -d interviewkit -f /docker-entrypoint-initdb.d/init.sql

# 6. Activate venv and start services
source ../../venv-ai/bin/activate
export PYTHONPATH=$(pwd)
bash scripts/start_dev.sh

# 7. Start frontend (new terminal)
cd frontend && npm run dev
```

### Access Points
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## Project Structure

```
ai_interviewer/
├── docs/              # Architecture docs & roadmap
├── frontend/          # Next.js frontend application
├── services/          # Backend microservices
│   ├── gateway/       # API Gateway — routing, CORS, auth
│   ├── auth/          # Authentication & user management
│   ├── resume_parser/ # Resume PDF/DOCX parsing + LLM structuring
│   ├── ai_engine/     # Core LLM orchestration (questions, rubrics, etc.)
│   ├── kit_manager/   # Kit lifecycle, storage, sharing
│   ├── pdf_generator/ # PDF generation from kit data
│   └── billing/       # Stripe billing & subscriptions
├── shared/            # Shared infrastructure
│   ├── config/        # Base settings (loads .env)
│   ├── database/      # Common DB connector & models
│   ├── middleware/     # Error handling
│   ├── schemas/       # Shared Pydantic schemas
│   └── utils/         # Logging, Redis, security utilities
├── scripts/           # Setup & dev scripts
├── data/              # Uploads, outputs, temp files
├── .env.example       # Environment template
├── docker-compose.yml # Local dev infrastructure
└── requirements.txt   # Python dependencies
```

## Development

### Running Individual Services
```bash
# Activate venv
source ../../venv-ai/bin/activate
export PYTHONPATH=$(pwd)

# Start a single service
uvicorn services.ai_engine.app:app --reload --port 8003
```

### Running Tests
```bash
pytest tests/
pytest tests/unit/test_auth.py -v
```

### Environment Variables
See [.env.example](.env.example) for all configuration options. At minimum you need:
- `ANTHROPIC_API_KEY` — for AI generation
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.11), async |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| AI/LLM | Anthropic Claude API |
| PDF | WeasyPrint + Jinja2 |
| Auth | JWT + bcrypt |
| DevOps | Docker, Docker Compose |
