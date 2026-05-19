# InterviewKit AI — Microservices Architecture

## System Design Overview

The application is divided into **independent microservices** that communicate via REST APIs and a shared message queue for async operations. Each service is independently deployable, testable, and scalable.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│                   React + Tailwind + TypeScript                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP/WebSocket
┌──────────────────────────────▼──────────────────────────────────┐
│                      API GATEWAY SERVICE                          │
│              FastAPI — Routing, Rate Limiting, CORS               │
└──┬──────┬──────────┬──────────┬──────────┬──────────┬───────────┘
   │      │          │          │          │          │
   ▼      ▼          ▼          ▼          ▼          ▼
┌─────┐┌──────┐┌──────────┐┌────────┐┌─────────┐┌─────────┐
│AUTH ││RESUME││ AI_ENGINE ││  KIT   ││   PDF   ││ BILLING │
│SVC  ││PARSER││  SERVICE  ││MANAGER ││GENERATOR││ SERVICE │
└─────┘└──────┘└──────────┘└────────┘└─────────┘└─────────┘
   │      │          │          │          │          │
   └──────┴──────────┴──────┬───┴──────────┴──────────┘
                             │
              ┌──────────────▼──────────────┐
              │    SHARED DATABASE LAYER     │
              │   PostgreSQL + Redis Cache   │
              └─────────────────────────────┘
```

---

## Service Breakdown

### 1. API Gateway (`services/gateway/`)
**Responsibility:** Single entry point for all client requests.
- Request routing to downstream services
- Rate limiting (per user, per IP)
- CORS handling
- Request/response logging
- Health check aggregation
- JWT token validation (delegates to Auth service)

**Tech:** FastAPI, httpx (async HTTP client), Redis (rate limiting)

---

### 2. Auth Service (`services/auth/`)
**Responsibility:** User authentication and authorization.
- User registration (email + password)
- OAuth2 (Google)
- JWT token issuance and validation
- Session management
- Password reset flow
- User profile management

**Tech:** FastAPI, python-jose (JWT), passlib (password hashing), OAuth2 lib

---

### 3. Resume Parser Service (`services/resume_parser/`)
**Responsibility:** Extract and structure resume data.
- PDF text extraction (PyMuPDF)
- DOCX text extraction (python-docx)
- Raw text → LLM → Structured JSON (skills, experience, projects, etc.)
- File upload handling and storage
- Resume caching (avoid re-parsing)

**Tech:** FastAPI, PyMuPDF, python-docx, Claude/OpenAI API

---

### 4. AI Engine Service (`services/ai_engine/`)
**Responsibility:** Core LLM orchestration for interview kit generation.
- JD analysis and structuring
- Question generation with model answers
- Practical assessment generation
- Scoring rubric generation
- Red flags identification
- Interview flow guide creation
- Prompt template management and versioning
- Parallel LLM call orchestration

**Tech:** FastAPI, anthropic SDK, openai SDK, asyncio for parallel calls

---

### 5. Kit Manager Service (`services/kit_manager/`)
**Responsibility:** Kit lifecycle management.
- Kit creation workflow orchestration
- Kit storage and retrieval
- Kit history and search
- Shareable link generation
- Kit versioning
- Candidate comparison logic
- Debrief form generation

**Tech:** FastAPI, SQLAlchemy, async orchestration

---

### 6. PDF Generator Service (`services/pdf_generator/`)
**Responsibility:** Generate downloadable PDF kits.
- HTML template rendering
- PDF generation from structured kit data
- Branded templates
- Caching generated PDFs
- Async generation with webhook callback

**Tech:** FastAPI, WeasyPrint or reportlab, Jinja2 templates

---

### 7. Billing Service (`services/billing/`)
**Responsibility:** Subscription and usage management.
- Stripe integration (subscriptions, checkout)
- Usage tracking (kits generated per user)
- Plan management (Free/Pro/Team)
- Webhook handling for Stripe events
- Invoice generation

**Tech:** FastAPI, stripe SDK

---

## Shared Infrastructure (`shared/`)

### Database (`shared/database/`)
- Common SQLAlchemy connection pooling
- Base models and migrations (Alembic)
- Connection factory with env-based config

### Config (`shared/config/`)
- Central .env loading
- Base settings class (Pydantic BaseSettings)
- Each service extends with its own config

### Models (`shared/models/`)
- Shared Pydantic schemas for inter-service communication
- Database ORM models
- Common response/error schemas

### Utils (`shared/utils/`)
- Logging configuration
- Error handling middleware
- Common decorators (retry, cache, timing)

---

## Communication Patterns

| Pattern | Use Case |
|---------|----------|
| Sync REST | Gateway → Auth (token validation) |
| Sync REST | Gateway → Kit Manager (CRUD operations) |
| Async Queue (Redis) | Kit Manager → AI Engine (kit generation) |
| Async Queue (Redis) | Kit Manager → PDF Generator (PDF creation) |
| Webhook/Callback | Billing → Kit Manager (plan changes) |
| WebSocket | Frontend ← Gateway (streaming generation progress) |

---

## Data Flow: Kit Generation

```
1. User uploads JD + Resume via Frontend
2. Frontend → Gateway → Kit Manager (create kit request)
3. Kit Manager → Resume Parser (parse resume)
4. Kit Manager → AI Engine (analyze JD)
5. Kit Manager → AI Engine (parallel generation):
   ├── Generate Questions + Model Answers
   ├── Generate Practical Assessment
   ├── Generate Scoring Rubric
   ├── Identify Red Flags
   └── Create Interview Flow Guide
6. AI Engine streams progress → Kit Manager → Gateway → Frontend (WebSocket)
7. Kit Manager assembles final kit → stores in DB
8. Kit Manager → PDF Generator (async PDF creation)
9. Frontend receives complete kit + PDF download link
```

---

## Database Schema (High-Level)

```sql
users               → id, email, name, password_hash, oauth_provider, plan, created_at
teams               → id, name, owner_id, created_at
team_members        → team_id, user_id, role
kits                → id, user_id, team_id, jd_text, status, created_at
kit_results         → kit_id, section_type, content_json, version
resumes             → id, user_id, filename, raw_text, structured_json, created_at
usage_records       → id, user_id, action_type, kit_id, created_at
feedback            → id, kit_id, user_id, rating, comments, created_at
prompt_templates    → id, role_type, section_type, template_text, version, is_active
subscriptions       → id, user_id, stripe_sub_id, plan, status, current_period_end
```

---

## Scalability Strategy

1. **Horizontal Scaling:** Each service runs independently; scale AI Engine and PDF Generator based on load
2. **Queue-Based Decoupling:** Redis queues between Kit Manager ↔ AI Engine prevent cascading failures
3. **Caching:** Redis caches parsed resumes, generated PDFs, and frequently-accessed kits
4. **Connection Pooling:** Shared DB connector uses async connection pools (asyncpg)
5. **Rate Limiting:** Per-user and per-plan limits at Gateway level

---

## Deployment Strategy

| Component | Platform | Reason |
|-----------|----------|--------|
| Frontend | Vercel | Zero-config Next.js hosting, edge CDN |
| Gateway + Services | Railway / Docker | Easy container deployment, auto-scaling |
| Database | Supabase / Railway PostgreSQL | Managed PostgreSQL with backups |
| Redis | Railway Redis / Upstash | Managed Redis for queues + caching |
| File Storage | Supabase Storage / S3 | Resume uploads and generated PDFs |
