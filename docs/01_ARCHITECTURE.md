# InterviewKit AI — Microservices Architecture

## Overview

InterviewKit AI is an AI-powered interview preparation kit generator for technical hiring.  
**Input:** Job Description + Candidate Resume  
**Output:** Complete interview kit (questions, practical test, rubric, red flags, flow guide, PDF)

This document defines the microservices architecture with clear service boundaries, independence, and concurrency.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│   Browser (Next.js SSR/CSR)  │  Mobile (future)  │  API consumers (future)  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY SERVICE                                  │
│   FastAPI  │  Auth verification  │  Rate limiting  │  Request routing        │
│   JWT validation  │  API key management  │  CORS  │  Request logging         │
└────┬──────────┬──────────────┬───────────────┬──────────────┬───────────────┘
     │          │              │               │              │
     ▼          ▼              ▼               ▼              ▼
┌─────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  AUTH   │ │  RESUME  │ │  AI ENGINE   │ │   KIT    │ │   EXPORT     │
│ SERVICE │ │  SERVICE │ │   SERVICE    │ │  ORCH.   │ │   SERVICE    │
│         │ │          │ │              │ │  SERVICE │ │              │
│ FastAPI │ │ FastAPI  │ │   FastAPI    │ │ FastAPI  │ │   FastAPI    │
└────┬────┘ └────┬─────┘ └──────┬───────┘ └────┬─────┘ └──────┬───────┘
     │           │               │              │              │
     ▼           ▼               ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SHARED INFRASTRUCTURE                                │
│   PostgreSQL (Supabase)  │  Redis (cache/queue)  │  S3/MinIO (file storage) │
│   RabbitMQ / Redis Streams (async messaging)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Services Breakdown

### 1. Frontend Service
| Property | Value |
|----------|-------|
| **Language** | TypeScript |
| **Framework** | Next.js 14 (App Router) + Tailwind CSS |
| **Responsibilities** | UI/UX, client-side logic, SSR, file uploads, streaming responses |
| **Port** | 3000 |
| **Deployed on** | Vercel |

**Key modules:**
- Landing page + waitlist capture
- JD + Resume input UI (drag-drop, paste)
- Kit display with interactive cards
- Dashboard (kit history, search, filter)
- Team workspace UI
- PDF download trigger
- Real-time streaming of AI generation progress

---

### 2. API Gateway Service
| Property | Value |
|----------|-------|
| **Language** | Python |
| **Framework** | FastAPI |
| **Responsibilities** | Auth verification, rate limiting, request routing, API versioning |
| **Port** | 8000 |
| **Deployed on** | Railway / AWS ECS |

**Key modules:**
- JWT token validation (delegates to Auth Service)
- Rate limiter (per user, per plan tier)
- Request router to internal services
- API key management for B2B API consumers
- Request/response logging
- Health checks aggregation

---

### 3. Auth Service
| Property | Value |
|----------|-------|
| **Language** | Python |
| **Framework** | FastAPI |
| **Responsibilities** | User registration, login, OAuth, session management, billing |
| **Port** | 8001 |
| **Database** | PostgreSQL (users, teams, subscriptions) |

**Key modules:**
- Email + password registration/login
- Google OAuth integration
- JWT token generation + refresh
- Team/workspace management
- Usage tracking (kits generated per month)
- Stripe subscription integration
- Plan enforcement (free tier limits)

---

### 4. Resume Service
| Property | Value |
|----------|-------|
| **Language** | Python |
| **Framework** | FastAPI |
| **Responsibilities** | Resume parsing, text extraction, structured data output |
| **Port** | 8002 |
| **Dependencies** | PyMuPDF, python-docx, LLM client |

**Key modules:**
- PDF text extraction (PyMuPDF)
- DOCX text extraction (python-docx)
- Raw text → structured JSON via LLM
- Output schema: `{ skills, experience_level, tech_stack, projects, education, employment_timeline, gaps }`
- File validation (size, type, malware scan)
- Caching (same resume hash → cached result)

**API:**
```
POST /parse
  Input: file (PDF/DOCX) or raw text
  Output: { structured_resume: {...}, raw_text: str, confidence: float }
```

---

### 5. AI Engine Service
| Property | Value |
|----------|-------|
| **Language** | Python |
| **Framework** | FastAPI |
| **Responsibilities** | All LLM interactions — question gen, practical test, rubric, red flags, flow guide |
| **Port** | 8003 |
| **Dependencies** | Anthropic SDK, OpenAI SDK (fallback), prompt templates |

**Key modules:**
- **Prompt Manager:** Versioned prompt templates per role type, A/B testing
- **JD Analyzer:** JD text → `{ required_skills, seniority, responsibilities, nice_to_haves }`
- **Question Generator:** Resume + JD → 8-12 tailored questions with model answers
- **Practical Test Generator:** Role-specific practical assessments with 3 difficulty variants
- **Rubric Generator:** Weighted scoring rubric with calibration examples
- **Red Flags Analyzer:** Resume concerns + diplomatic probe questions
- **Flow Guide Generator:** Minute-by-minute interview structure
- **Match Scorer:** Resume × JD skill match analysis

**API:**
```
POST /analyze-jd         → structured JD
POST /generate-questions → questions with model answers
POST /generate-test      → practical assessment
POST /generate-rubric    → scoring rubric
POST /analyze-red-flags  → red flags + probes
POST /generate-flow      → interview flow guide
POST /match-score        → resume-JD match analysis
```

**Concurrency:** All generation endpoints are independent and can run in parallel.

---

### 6. Kit Orchestrator Service
| Property | Value |
|----------|-------|
| **Language** | Python |
| **Framework** | FastAPI |
| **Responsibilities** | Pipeline orchestration, parallel execution, kit assembly, storage |
| **Port** | 8004 |
| **Dependencies** | Redis (job queue), all internal services |

**Key modules:**
- **Pipeline Controller:** Orchestrates the full generation pipeline
- **Parallel Executor:** Fires concurrent requests to AI Engine (questions + test + rubric + flags + flow)
- **Kit Assembler:** Collects all outputs into a unified kit JSON
- **Kit Storage:** Persists assembled kits to PostgreSQL
- **Status Tracker:** Real-time status updates via WebSocket/SSE
- **Retry Logic:** Handles partial failures, retries individual steps

**Pipeline Flow:**
```
1. Receive (JD + Resume + role_type + user_id)
2. PARALLEL:
   a. Resume Service → parse resume → structured_resume
   b. AI Engine → analyze JD → structured_jd
3. WAIT for 2a + 2b
4. AI Engine → match_score(structured_resume, structured_jd)
5. PARALLEL (all receive match context):
   a. AI Engine → generate_questions
   b. AI Engine → generate_test
   c. AI Engine → generate_rubric
   d. AI Engine → analyze_red_flags
   e. AI Engine → generate_flow
6. WAIT for 5a-5e
7. Assemble kit → store in DB → return kit_id
8. Push status update to client via SSE
```

---

### 7. Export Service
| Property | Value |
|----------|-------|
| **Language** | Python |
| **Framework** | FastAPI |
| **Responsibilities** | PDF generation, export formats, shareable links |
| **Port** | 8005 |
| **Dependencies** | WeasyPrint or Playwright (headless), Jinja2 templates |

**Key modules:**
- PDF renderer (kit JSON → branded PDF)
- HTML template engine (Jinja2)
- Shareable link generation (UUID-based public routes)
- Export queue (async PDF generation for heavy load)
- Cache layer (generated PDFs cached for 24h)

**API:**
```
POST /generate-pdf    → { pdf_url: str, expires_at: datetime }
GET  /download/{id}   → PDF file stream
POST /share-link      → { share_url: str, access_token: str }
```

---

## Inter-Service Communication

| Pattern | Use Case |
|---------|----------|
| **Sync REST** | Frontend → Gateway → internal services (user-facing requests) |
| **Async Message Queue** | Kit generation pipeline (Redis Streams / RabbitMQ) |
| **SSE (Server-Sent Events)** | Real-time progress updates to frontend |
| **Webhook** | Stripe payment events, external integrations |

---

## Data Flow

```
User uploads JD + Resume
        │
        ▼
  [API Gateway] ─── validates auth, rate limit
        │
        ▼
  [Kit Orchestrator] ─── creates job, returns job_id
        │
        ├──► [Resume Service] ─── parses resume (2-4s)
        │         │
        │         ▼
        │    structured_resume
        │
        ├──► [AI Engine: JD Analysis] ─── parses JD (1-2s)
        │         │
        │         ▼
        │    structured_jd
        │
        ▼ (waits for both)
  [AI Engine: Match Score] ─── (1-2s)
        │
        ▼
  PARALLEL GENERATION (8-12s total):
        ├──► Questions (5-8s)
        ├──► Practical Test (5-8s)
        ├──► Rubric (3-5s)
        ├──► Red Flags (2-3s)
        └──► Flow Guide (1-2s)
        │
        ▼ (waits for all)
  [Kit Orchestrator] ─── assembles kit, stores in DB
        │
        ▼
  SSE push to frontend → Kit rendered in UI
```

**Total time: 15-25 seconds (perceived ~10s with streaming UI)**

---

## Database Schema (High-Level)

```sql
-- Auth Service owns:
users, teams, team_members, subscriptions, usage_logs

-- Kit Orchestrator owns:
kits, kit_sections, generation_jobs

-- Resume Service owns:
parsed_resumes (cached)

-- AI Engine owns:
prompt_templates, prompt_versions, feedback

-- Export Service owns:
exports, share_links
```

Each service owns its own tables. No cross-service direct DB access. Services communicate only via APIs.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, React Query |
| API Gateway | Python, FastAPI, Redis (rate limiting) |
| Backend Services | Python, FastAPI, Pydantic, asyncio |
| LLM | Anthropic Claude API (primary), OpenAI GPT-4 (fallback) |
| Database | PostgreSQL (via Supabase) |
| Cache | Redis |
| Message Queue | Redis Streams (MVP) → RabbitMQ (scale) |
| File Storage | Supabase Storage / S3 |
| PDF Generation | WeasyPrint / Playwright |
| Auth | JWT + OAuth2 (Supabase Auth or custom) |
| Payments | Stripe |
| Monitoring | Sentry + PostHog |
| CI/CD | GitHub Actions |
| Containers | Docker + docker-compose (local), Railway/Render (prod) |

---

## Service Independence Rules

1. **No shared databases between services** — each service owns its data
2. **Services communicate via HTTP APIs or message queues** — never direct DB queries
3. **Each service is independently deployable** — own Dockerfile, own CI pipeline
4. **Each service has its own test suite** — unit + integration tests
5. **Failure isolation** — one service going down doesn't crash others (graceful degradation)
6. **Shared libraries are extracted as packages** — common schemas, auth utils

---

## Repository Structure

```
ai_interviewer/
├── docs/                          # Documentation (you are here)
├── shared/                        # Shared Python package (schemas, utils)
│   ├── schemas/                   # Pydantic models shared across services
│   ├── auth/                      # JWT verification utilities
│   └── config/                    # Shared config loading
├── services/
│   ├── gateway/                   # API Gateway Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   └── config.py
│   │   └── tests/
│   ├── auth/                      # Auth Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── config.py
│   │   └── tests/
│   ├── resume/                    # Resume Parser Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── parser/
│   │   │   ├── routes/
│   │   │   └── config.py
│   │   └── tests/
│   ├── ai_engine/                 # AI Engine Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── prompts/           # Versioned prompt templates
│   │   │   ├── generators/        # Question, test, rubric generators
│   │   │   ├── routes/
│   │   │   └── config.py
│   │   └── tests/
│   ├── kit_orchestrator/          # Kit Orchestrator Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── pipeline/
│   │   │   ├── routes/
│   │   │   └── config.py
│   │   └── tests/
│   └── export/                    # Export Service
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── app/
│       │   ├── main.py
│       │   ├── templates/         # PDF/HTML templates
│       │   ├── routes/
│       │   └── config.py
│       └── tests/
├── frontend/                      # Next.js Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── services/              # API client layer
│   │   └── types/
│   └── tests/
├── infrastructure/
│   ├── docker-compose.yml         # Local dev: all services
│   ├── docker-compose.prod.yml
│   └── nginx.conf                 # Reverse proxy config
├── scripts/
│   ├── setup.sh                   # First-time dev setup
│   ├── seed_db.sh                 # Seed development data
│   └── run_all.sh                 # Start all services locally
└── .github/
    └── workflows/
        ├── ci.yml                 # Lint + test all services
        └── deploy.yml             # Deploy on merge to main
```

---

## Concurrency Model

| Level | Strategy |
|-------|----------|
| **Request-level** | FastAPI async handlers (asyncio) |
| **Service-level** | Multiple service instances behind load balancer |
| **Pipeline-level** | Parallel LLM calls within Kit Orchestrator (asyncio.gather) |
| **Queue-level** | Background workers consuming from Redis Streams |

---

## Deployment Strategy

### Local Development
```bash
docker-compose up  # Starts all services + Postgres + Redis
```

### Production (MVP)
- **Frontend:** Vercel (free tier)
- **Backend services:** Railway (each service = separate Railway service)
- **Database:** Supabase (free → Pro at scale)
- **Redis:** Railway Redis or Upstash
- **File Storage:** Supabase Storage

### Production (Scale)
- **Frontend:** Vercel Pro
- **Backend:** AWS ECS or Kubernetes
- **Database:** RDS PostgreSQL
- **Redis:** ElastiCache
- **Queue:** Amazon SQS or RabbitMQ
- **CDN:** CloudFront for static assets + PDF caching
