# InterviewKit AI — Implementation Plan

## Repository Structure

```
ai_interviewer/
├── docs/                              # Documentation
│   ├── 01_ROADMAP.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_MICROSERVICES_DESIGN.md
│   └── 04_IMPLEMENTATION_PLAN.md
│
├── frontend/                          # Next.js Frontend Application
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── public/
│   ├── src/
│   │   ├── app/                       # Next.js App Router
│   │   ├── components/                # Reusable UI components
│   │   ├── lib/                       # API client, utilities
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── stores/                    # State management
│   │   └── types/                     # TypeScript types
│   └── config/
│       └── config.ts                  # Frontend config
│
├── services/                          # Backend Microservices
│   ├── gateway/                       # API Gateway
│   │   ├── __init__.py
│   │   ├── app.py                     # FastAPI app
│   │   ├── routes.py                  # Route definitions
│   │   ├── middleware.py              # Rate limiting, CORS, logging
│   │   └── config/
│   │       └── settings.py            # Gateway-specific config
│   │
│   ├── auth/                          # Auth Service
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── service.py                 # Business logic
│   │   ├── models.py                  # Auth-specific DB models
│   │   ├── schemas.py                 # Request/Response schemas
│   │   ├── utils.py                   # JWT, hashing utilities
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── resume_parser/                 # Resume Parser Service
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── parsers/                   # PDF, DOCX parsers
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py
│   │   │   └── docx_parser.py
│   │   ├── schemas.py
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── ai_engine/                     # AI Engine Service
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── service.py                 # Orchestration logic
│   │   ├── prompts/                   # Prompt templates
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── questions.py
│   │   │   ├── assessment.py
│   │   │   ├── rubric.py
│   │   │   ├── red_flags.py
│   │   │   └── flow_guide.py
│   │   ├── llm/                       # LLM client abstraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── claude_client.py
│   │   │   └── openai_client.py
│   │   ├── schemas.py
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── kit_manager/                   # Kit Manager Service
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── orchestrator.py            # Kit generation orchestration
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── pdf_generator/                 # PDF Generator Service
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── templates/                 # HTML/Jinja2 templates for PDF
│   │   │   └── kit_template.html
│   │   ├── schemas.py
│   │   └── config/
│   │       └── settings.py
│   │
│   └── billing/                       # Billing Service
│       ├── __init__.py
│       ├── app.py
│       ├── routes.py
│       ├── service.py
│       ├── models.py
│       ├── schemas.py
│       └── config/
│           └── settings.py
│
├── shared/                            # Shared Infrastructure Code
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connector.py               # Common async DB connector
│   │   ├── base_model.py              # SQLAlchemy base model
│   │   └── migrations/                # Alembic migrations
│   │       ├── env.py
│   │       └── versions/
│   ├── config/
│   │   ├── __init__.py
│   │   └── base_settings.py           # Base Pydantic settings (loads .env)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py                  # Common response schemas
│   │   └── events.py                  # Inter-service event schemas
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py           # Global error handling
│   │   └── logging_middleware.py      # Request logging
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                  # Structured logging setup
│       ├── redis_client.py            # Shared Redis client
│       └── security.py               # Common security utilities
│
├── scripts/
│   ├── setup.sh                       # Project setup script
│   ├── start_dev.sh                   # Start all services for dev
│   └── init_db.sql                    # Initial DB schema
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared test fixtures
│   ├── unit/                          # Unit tests per service
│   ├── integration/                   # Integration tests
│   └── e2e/                           # End-to-end tests
│
├── .env.example                       # Environment variable template
├── .gitignore
├── docker-compose.yml                 # Local development orchestration
├── alembic.ini                        # Alembic config
├── pyproject.toml                     # Python project config
├── requirements.txt                   # Python dependencies
└── README.md
```

---

## Implementation Order (Phase 1 MVP)

### Sprint 1: Foundation (Days 1–3)
1. ✅ Set up repository structure
2. ✅ Implement shared modules (DB connector, config, logging)
3. ✅ Set up Docker Compose for local dev
4. ✅ Database schema + migrations
5. ✅ Auth service (register, login, JWT)

### Sprint 2: Core Pipeline (Days 4–8)
1. Resume Parser service (PDF + DOCX extraction + LLM structuring)
2. AI Engine service (prompt templates + LLM clients + all generators)
3. Kit Manager service (orchestration + storage)

### Sprint 3: Output & Frontend (Days 9–14)
1. PDF Generator service
2. Gateway service (routing + rate limiting)
3. Frontend: Input UI (JD + Resume upload)
4. Frontend: Kit display with all sections
5. Frontend: PDF download

### Sprint 4: Polish & Deploy (Days 15–18)
1. Frontend: Auth pages (login/register)
2. Frontend: Kit history dashboard
3. Usage limits implementation
4. End-to-end testing
5. Deployment setup

---

## What You Need To Do (Manual Steps)

1. **Create accounts:**
   - Anthropic API key (Claude) → https://console.anthropic.com
   - Stripe account → https://dashboard.stripe.com
   - Supabase project (or local PostgreSQL) → https://supabase.com
   - Vercel account (for frontend deployment) → https://vercel.com

2. **Set up .env file** with your actual API keys (see .env.example)

3. **Start PostgreSQL and Redis locally** (Docker Compose handles this)

4. **Run database migrations** after services are built

5. **Test with real resumes** — quality depends on prompt iteration

---

## Tech Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14 + TypeScript + Tailwind | Fast, SEO-ready, great DX |
| Backend Services | FastAPI (Python 3.11+) | Async, fast, great typing |
| Database | PostgreSQL | Reliable, feature-rich |
| Cache/Queue | Redis | Fast, pub/sub + caching |
| AI/LLM | Anthropic Claude API | Best structured output |
| PDF | WeasyPrint | CSS-based PDF generation |
| Auth | JWT + bcrypt | Stateless, scalable |
| Container | Docker + Docker Compose | Consistent environments |
| Testing | pytest + httpx | Async test support |
