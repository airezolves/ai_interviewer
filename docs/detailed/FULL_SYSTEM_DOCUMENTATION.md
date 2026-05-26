# InterviewKit AI — Complete System Documentation

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [End-to-End Flow](#3-end-to-end-flow)
4. [Service-by-Service Feature Breakdown](#4-service-by-service-feature-breakdown)
5. [Frontend Application](#5-frontend-application)
6. [Database Design](#6-database-design)
7. [Shared Infrastructure](#7-shared-infrastructure)
8. [Deployment & DevOps](#8-deployment--devops)
9. [Requirements & Dependencies](#9-requirements--dependencies)
10. [Improvements & Recommendations](#10-improvements--recommendations)
11. [Flowcharts](#11-flowcharts)

---

## 1. System Overview

**InterviewKit AI** is a full-stack AI-powered platform that generates comprehensive, personalized interview preparation kits for technical hiring. Given a Job Description (JD) and a candidate's resume, the system produces:

- **Tailored Interview Questions** (10 questions with model answers, follow-ups)
- **Practical Assessments** (3 difficulty variants: junior/mid/senior)
- **Weighted Scoring Rubric** (8 criteria, calibration examples)
- **Red Flags Analysis** (concerns + diplomatic probe questions)
- **Interview Flow Guide** (minute-by-minute 60-min structure)
- **Match Score** (resume-JD fit analysis with gaps & matches)
- **PDF Export** (one-click branded PDF download)

### Target Users
- **Hiring Managers** — prepare structured interviews for data/ML/engineering candidates
- **Recruiters** — generate standardized evaluation kits
- **Interview Panels** — shared scoring rubrics for consistency

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Zustand |
| Backend | Python, FastAPI (6 microservices) |
| Database | PostgreSQL (via Supabase) |
| Cache/Queue | Redis |
| LLM Providers | Anthropic Claude (primary), OpenAI GPT-4 (fallback) |
| PDF Generation | WeasyPrint + Jinja2 |
| Authentication | JWT (access + refresh tokens), bcrypt, Google OAuth |
| Deployment | Docker Compose, Vercel (FE), Railway (BE) |

---

## 2. Architecture

### Microservices Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 14)                        │
│                   Vercel / localhost:3000                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS / API calls
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Port 8000)                            │
│         JWT Auth Middleware │ Rate Limiting │ Request Routing         │
└──────┬──────────┬──────────┬──────────────────┬────────────────────┘
       │          │          │                  │
       ▼          ▼          ▼                  ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────┐
│   AUTH   │ │  RESUME  │ │    KIT       │ │  EXPORT  │
│  Service │ │  Service │ │ ORCHESTRATOR │ │  Service │
│  :8001   │ │  :8002   │ │    :8004     │ │  :8005   │
└──────────┘ └──────────┘ └──────┬───────┘ └──────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  RESUME  │ │AI ENGINE │ │AI ENGINE │
              │  Service │ │  :8003   │ │ (5 gen)  │
              │  :8002   │ │ analyze  │ │ parallel │
              └──────────┘ └──────────┘ └──────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE                                     │
│         PostgreSQL (:5432)  │  Redis (:6379)                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Port | Responsibility |
|---------|------|---------------|
| **API Gateway** | 8000 | Single entry point, JWT auth, rate limiting, routing |
| **Auth Service** | 8001 | Registration, login, OAuth, plan enforcement |
| **Resume Service** | 8002 | PDF/DOCX parsing → structured JSON |
| **AI Engine** | 8003 | All LLM interactions (7 generators) |
| **Kit Orchestrator** | 8004 | Pipeline orchestration, job tracking, SSE |
| **Export Service** | 8005 | PDF generation, shareable links |

---

## 3. End-to-End Flow

### Complete User Journey

```
┌──────────┐    ┌──────────┐    ┌──────────────────────────────────────┐
│  USER    │    │ FRONTEND │    │            BACKEND SERVICES           │
└────┬─────┘    └────┬─────┘    └───────────────────┬──────────────────┘
     │               │                              │
     │ 1. Visit app  │                              │
     │──────────────>│                              │
     │               │                              │
     │ 2. Login/Reg  │  POST /auth/register         │
     │──────────────>│─────────────────────────────>│ Auth Service
     │               │<─ JWT tokens ────────────────│
     │               │                              │
     │ 3. Upload     │                              │
     │    Resume +   │  POST /kits/generate         │
     │    Paste JD   │─────────────────────────────>│ Gateway → Orchestrator
     │──────────────>│<─ { job_id, kit_id } ────────│
     │               │                              │
     │               │  GET /kits/{id}/stream (SSE) │
     │  4. Watch     │─────────────────────────────>│ Orchestrator
     │  progress bar │<─ progress events ───────────│
     │<──────────────│                              │
     │               │                              │  ┌──────────────────┐
     │               │                              │  │ PIPELINE RUNS:   │
     │               │                              │  │ 1. Parse resume  │
     │               │                              │  │ 2. Analyze JD    │
     │               │                              │  │ 3. Match score   │
     │               │                              │  │ 4. Gen questions │
     │               │                              │  │ 5. Gen test      │
     │               │                              │  │ 6. Gen rubric    │
     │               │                              │  │ 7. Gen red flags │
     │               │                              │  │ 8. Gen flow      │
     │               │                              │  └──────────────────┘
     │               │                              │
     │ 5. View Kit   │  GET /kits/{kit_id}          │
     │<──────────────│─────────────────────────────>│ Orchestrator → DB
     │               │<─ Full kit JSON ─────────────│
     │               │                              │
     │ 6. Export PDF │  POST /export/pdf/{kit_id}   │
     │──────────────>│─────────────────────────────>│ Export Service
     │               │<─ PDF download URL ──────────│
     │<──────────────│                              │
     │               │                              │
     │ 7. Share Kit  │  POST /export/share/{kit_id} │
     │──────────────>│─────────────────────────────>│ Export Service
     │               │<─ { share_url } ─────────────│
     │<──────────────│                              │
```

### Pipeline Execution Detail (Kit Orchestrator)

```
START (POST /kits/generate received)
  │
  ├─ Create Kit record (status: pending)
  ├─ Create GenerationJob record (status: pending)
  ├─ Return { job_id, kit_id } to client immediately
  │
  ▼ (async background task)
  
Phase 1: INPUT PROCESSING [Parallel] ── progress: 10-25%
  ┌───────────────────┬────────────────────────┐
  │ Resume Service    │ AI Engine              │
  │ POST /parse       │ POST /analyze-jd       │
  │ → StructuredResume│ → StructuredJD         │
  └───────────────────┴────────────────────────┘
  
Phase 2: MATCH ANALYSIS ── progress: 25-35%
  │
  ├─ POST /match-score (resume + JD → match analysis)
  │   → { overall_match_score, skill_matches, skill_gaps }
  │
  ▼

Phase 3: KIT GENERATION [Parallel, 5 generators] ── progress: 35-85%
  ┌───────────────────────────────────────────────────────────┐
  │ POST /generate-questions  → 10 tailored questions         │
  │ POST /generate-test       → 3-variant practical test      │
  │ POST /generate-rubric     → 8-criteria scoring rubric     │
  │ POST /generate-red-flags  → 3-5 concerns + probes        │
  │ POST /generate-flow       → 60-min interview structure    │
  └───────────────────────────────────────────────────────────┘
  (asyncio.gather with return_exceptions=True for resilience)

Phase 4: ASSEMBLY ── progress: 85-100%
  │
  ├─ Update Kit record with all generated sections
  ├─ Set kit.status = "complete" (or "partial" if some generators failed)
  ├─ Update GenerationJob (status, completed_at)
  │
  ▼
DONE ─ SSE sends "complete" event to client
```

### Performance Targets

| Operation | Target | Actual Approach |
|-----------|--------|----------------|
| Total kit generation | < 25 seconds | Parallel LLM calls |
| Perceived wait time | < 10 seconds | SSE progress streaming |
| Resume parsing | < 4 seconds | PyMuPDF + LLM structuring |
| JD analysis | < 3 seconds | Single LLM call |
| Each generator | < 8 seconds | Async LLM with caching |
| PDF generation | < 5 seconds | WeasyPrint |
| Non-AI endpoints | < 200ms | Direct DB queries |

---

## 4. Service-by-Service Feature Breakdown

### 4.1 API Gateway (Port 8000)

**Purpose:** Single entry point for all client requests. Handles cross-cutting concerns.

#### Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Request Routing** | Proxies to correct microservice | FastAPI path-based routing |
| **JWT Authentication** | Verifies Bearer tokens on protected routes | `HTTPBearer` + `shared.auth.verify_token()` |
| **Rate Limiting** | Redis sliding-window counter per client | Middleware, 10 req/min (free), 60 req/min (pro) |
| **CORS** | Cross-origin support for frontend | FastAPI CORSMiddleware |
| **Health Checks** | `/health` endpoint for load balancers | Direct response |
| **Fail-Open** | If Redis down, requests still pass | try/except in rate limiter |

#### API Routes

```
POST /api/v1/auth/register    → Auth Service
POST /api/v1/auth/login       → Auth Service
POST /api/v1/auth/oauth/google → Auth Service
POST /api/v1/kits/generate    → Kit Orchestrator
GET  /api/v1/kits             → Kit Orchestrator
GET  /api/v1/kits/{id}        → Kit Orchestrator
GET  /api/v1/kits/{id}/stream → Kit Orchestrator (SSE)
DELETE /api/v1/kits/{id}      → Kit Orchestrator
POST /api/v1/export/pdf/{id}  → Export Service
GET  /api/v1/export/download/{id} → Export Service
POST /api/v1/export/share/{id} → Export Service
GET  /health                  → Direct (no auth)
```

#### Requirements to Implement
- FastAPI + Uvicorn
- Redis (for rate limiting)
- httpx (for async service-to-service calls)
- pyjwt (for token verification)

#### Improvements Needed
1. **Circuit breaker** — currently no circuit breaker if downstream services are unavailable
2. **Request tracing** — no correlation IDs for distributed tracing
3. **Logging** — needs structured JSON logging with request context
4. **API versioning** — currently hardcoded `/api/v1`, needs header-based versioning strategy
5. **Load balancing** — single gateway instance, needs horizontal scaling config
6. **Request validation** — should validate request bodies before proxying
7. **Response caching** — GET requests for kits could be cached
8. **IP-based + user-based rate limiting** — currently only IP-based

---

### 4.2 Auth Service (Port 8001)

**Purpose:** User identity management, authentication, and plan enforcement.

#### Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Email Registration** | Create account with email + password | bcrypt hashing, PostgreSQL |
| **Email Login** | Authenticate and receive JWT tokens | Access + Refresh token pair |
| **Google OAuth** | One-click Google login | OAuth2 code exchange |
| **JWT Token Management** | Access tokens (15 min), Refresh tokens (7 days) | pyjwt HS256 signing |
| **User Profile** | Get user details (name, email, plan) | GET endpoint |
| **Usage Tracking** | Track kits generated per month | Counter in users table |
| **Plan Enforcement** | Free tier: 3 kits/month limit | `/can-generate` check |

#### API Routes

```
POST /register              → Create user account
POST /login                 → Email + password → JWT tokens
POST /oauth/google          → Google OAuth → JWT tokens
GET  /users/{user_id}       → Get user profile
POST /users/{user_id}/increment-usage → Track kit generation
GET  /users/{user_id}/can-generate → Check free tier limit
```

#### Data Model (User)

```python
class User:
    id: UUID (PK)
    email: str (unique, indexed)
    password_hash: str (bcrypt)
    name: str
    auth_provider: "email" | "google"
    plan: "free" | "pro" | "enterprise"
    kits_generated_this_month: int
    created_at: datetime
    updated_at: datetime
```

#### Requirements to Implement
- FastAPI + Uvicorn
- passlib + bcrypt (password hashing)
- pyjwt (token generation)
- httpx (Google OAuth verification)
- SQLAlchemy + asyncpg (PostgreSQL)

#### Improvements Needed
1. **Refresh token rotation** — store refresh tokens in DB and rotate on use
2. **Email verification** — no email confirmation flow exists
3. **Password reset** — no forgot-password functionality
4. **Account lockout** — no protection against brute-force login attempts
5. **Token revocation** — no blacklist for invalidated tokens
6. **OAuth providers** — only Google; add GitHub, LinkedIn
7. **MFA/2FA** — no multi-factor authentication option
8. **Session management** — no active-sessions list or remote logout
9. **Plan upgrade flow** — no Stripe integration for upgrading to Pro
10. **Monthly counter reset** — needs a cron job or scheduled task

---

### 4.3 Resume Service (Port 8002)

**Purpose:** Parse uploaded resumes (PDF/DOCX) into structured JSON using LLM.

#### Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **PDF Parsing** | Extract text from PDF files | PyMuPDF (fitz) |
| **DOCX Parsing** | Extract text from Word documents | python-docx |
| **LLM Structuring** | Convert raw text → structured data | Claude API call |
| **File Hash Caching** | Skip re-parsing identical files | SHA256 hash → DB lookup |
| **Text Input** | Accept raw pasted text (no file) | Direct LLM structuring |
| **Fallback** | Basic extraction if LLM fails | Regex-based parsing |

#### API Routes

```
POST /parse
  Body: multipart/form-data (file) OR JSON (raw_text)
  Response: StructuredResume
```

#### Output Schema (StructuredResume)

```python
class StructuredResume:
    skills: List[str]                    # ["Python", "TensorFlow", "SQL"]
    experience_level: str                # "junior" | "mid" | "senior"
    years_of_experience: float           # 5.5
    tech_stack: List[str]                # ["Python", "AWS", "Docker"]
    projects: List[Project]              # [{name, description, technologies}]
    education: List[Education]           # [{degree, institution, year, field}]
    employment_timeline: List[Employment] # [{company, role, duration, responsibilities}]
    gaps: List[str]                      # ["6-month gap between X and Y"]
    summary: str                         # 2-sentence professional summary
    raw_text: str                        # Original extracted text
```

#### Processing Pipeline

```
File Upload → Extract Text → Hash Check → LLM Structure → Cache → Return
                  │                │
                  │          (cache hit)
                  │                └─── Return cached result
                  │
           PyMuPDF (PDF)
           python-docx (DOCX)
```

#### Requirements to Implement
- FastAPI + Uvicorn + python-multipart
- PyMuPDF (fitz) — PDF text extraction
- python-docx — DOCX text extraction
- anthropic — LLM API for structuring
- hashlib — file deduplication
- SQLAlchemy + asyncpg — caching parsed results

#### Improvements Needed
1. **OCR support** — scanned PDFs currently return empty text
2. **More formats** — support .txt, .rtf, Google Docs links
3. **File size limit** — no enforcement of max file size (could OOM)
4. **Virus scanning** — uploaded files not scanned for malware
5. **Structured extraction** — use document layout analysis for better tables/lists
6. **Multilingual** — no handling of non-English resumes
7. **PII detection** — no warning about sensitive data (phone, SSN)
8. **Confidence scores** — LLM structuring doesn't report confidence per field
9. **Parser selection** — hardcoded parsers, should auto-detect best approach
10. **Async file upload** — large files could block the event loop

---

### 4.4 AI Engine Service (Port 8003)

**Purpose:** All LLM interactions — the "brain" of the system with 7 specialized generators.

#### Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **LLM Client** | Unified interface with fallback | Claude → GPT-4 auto-fallback |
| **JD Analyzer** | Parse job description → structured data | LLM prompt → StructuredJD |
| **Match Scorer** | Resume-JD compatibility analysis | LLM comparative analysis |
| **Question Generator** | 10 tailored interview questions | LLM with role context |
| **Test Generator** | Practical assessment (3 variants) | LLM with domain context |
| **Rubric Generator** | 8-criteria scoring system | LLM with JD priorities |
| **Red Flags Generator** | 3-5 concerns + probe questions | LLM risk analysis |
| **Flow Generator** | 60-min interview timeline | LLM scheduling |

#### API Routes

```
POST /analyze-jd           → StructuredJD
POST /match-score          → MatchAnalysis
POST /generate-questions   → List[Question]
POST /generate-test        → PracticalTest
POST /generate-rubric      → Rubric
POST /generate-red-flags   → List[RedFlag]
POST /generate-flow        → List[FlowSection]
```

#### Generator Details

##### 4.4.1 JD Analyzer
- **Input:** Raw JD text
- **Output:** `StructuredJD` — required_skills, nice_to_have_skills, seniority, responsibilities, company_info, team_size
- **Prompt strategy:** Extract structured data from unstructured JD text

##### 4.4.2 Match Scorer
- **Input:** StructuredResume + StructuredJD + role_type
- **Output:** `MatchAnalysis` — overall_match_score (0-100%), skill_matches, skill_gaps, experience_fit, recommendation
- **Prompt strategy:** Compare candidate qualifications against JD requirements

##### 4.4.3 Question Generator
- **Input:** StructuredResume + StructuredJD + MatchAnalysis + role_type
- **Output:** 10 `Question` objects
- **Question distribution:** 3 behavioral, 5 technical, 2 system_design
- **Each question includes:**
  - `question` — the actual question text
  - `category` — behavioral/technical/system_design
  - `what_it_tests` — skill/trait being evaluated
  - `model_answer` — ideal 2-3 sentence answer
  - `follow_up_probes` — 2-3 follow-up questions
  - `difficulty` — easy/medium/hard
- **Personalization:** Based on candidate's actual experience, tech stack, and identified gaps
- **Fallback:** 2 generic questions if LLM fails

##### 4.4.4 Practical Test Generator
- **Input:** StructuredResume + StructuredJD + MatchAnalysis + role_type
- **Output:** `PracticalTest` with 3 `PracticalTestVariant` objects
- **Each variant includes:**
  - `difficulty` — junior/mid/senior
  - `task_description` — detailed task specification
  - `dataset_scenario` — data/scenario context
  - `expected_deliverables` — list of outputs
  - `time_limit` — recommended completion time
  - `evaluation_criteria` — grading criteria
- **Role-specific contexts:**
  - data_scientist → EDA + modeling task
  - ml_engineer → ML pipeline design
  - data_analyst → analysis & visualization
  - data_engineer → ETL pipeline design
  - analytics_engineer → dbt modeling task

##### 4.4.5 Rubric Generator
- **Input:** StructuredJD + role_type + seniority
- **Output:** `Rubric` with 8 `RubricCriterion` objects
- **Each criterion:**
  - `name` — criterion name
  - `weight_pct` — percentage (all sum to 100)
  - `description` — what it evaluates
  - `score_1` — what poor looks like
  - `score_3` — what adequate looks like
  - `score_5` — what excellent looks like
- **Includes:** `pass_threshold` (typically 3.0-3.5)

##### 4.4.6 Red Flags Generator
- **Input:** StructuredResume + StructuredJD + MatchAnalysis
- **Output:** 3-5 `RedFlag` objects
- **Each flag:**
  - `concern` — the identified concern
  - `severity` — low/medium/high
  - `probe_question` — diplomatic investigation question
  - `what_to_listen_for` — response indicators
- **Analyzes:** Employment gaps, skill mismatches, short tenures, unclear contributions, over/under-qualification

##### 4.4.7 Flow Guide Generator
- **Input:** role_type + experience_level + seniority
- **Output:** 5 `FlowSection` objects (total = 60 minutes)
- **Standard structure:**
  - Introduction & rapport (5 min)
  - Background & experience (10 min)
  - Technical deep-dive (20 min)
  - Practical/system design (15 min)
  - Candidate questions & close (10 min)
- **Maps questions** to sections by index (0-9)

#### LLM Client Architecture

```python
class LLMClient:
    # Primary: Anthropic Claude (claude-3-5-sonnet)
    # Fallback: OpenAI GPT-4

    async def generate(prompt, system, temperature, max_tokens) → str
    async def generate_json(prompt, system, temperature, max_tokens) → dict|list
```

**Fallback Strategy:**
1. Try Claude → if rate limited / error → try GPT-4 → if error → raise RuntimeError
2. JSON parsing: strip markdown fences, parse JSON
3. Each generator has its own hardcoded fallback response if all LLM calls fail

#### Requirements to Implement
- FastAPI + Uvicorn
- anthropic — Anthropic Claude SDK
- openai — OpenAI GPT-4 SDK
- pydantic — response validation
- json — response parsing

#### Improvements Needed
1. **Prompt versioning** — prompts are hardcoded; need versioned prompt templates
2. **Output validation** — LLM output isn't validated against Pydantic schemas before return
3. **Retry logic** — no exponential backoff on rate limits
4. **Token counting** — no token budget management
5. **Response caching** — identical inputs should return cached results
6. **Streaming** — generators don't stream intermediate results
7. **Quality scoring** — no automated quality check on generated content
8. **A/B testing** — no mechanism to test different prompt variants
9. **Cost tracking** — no LLM cost monitoring per request
10. **Model selection** — hardcoded models; should be configurable per generator
11. **Temperature tuning** — same temperature for all tasks; should vary by task type
12. **Structured outputs** — use Anthropic/OpenAI structured output mode instead of text parsing

---

### 4.5 Kit Orchestrator Service (Port 8004)

**Purpose:** Orchestrate the full kit generation pipeline, manage jobs, and stream progress.

#### Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Pipeline Orchestration** | 4-phase execution with parallelism | asyncio.gather |
| **Job Tracking** | Real-time status + progress percentage | GenerationJob model |
| **SSE Streaming** | Push progress to client in real-time | Server-Sent Events |
| **Partial Success** | Kit can be "partial" if some generators fail | return_exceptions=True |
| **Kit CRUD** | Create, read, list, delete kits | PostgreSQL via SQLAlchemy |
| **Pagination** | List kits with offset/limit | SQL OFFSET/LIMIT |
| **Sharing** | Generate unique share tokens | UUID-based tokens |
| **State Machine** | pending → generating → complete/partial/failed | Status enum |

#### API Routes

```
POST /generate              → Start pipeline (returns job_id + kit_id)
GET  /kits                  → List user's kits (paginated)
GET  /kits/{kit_id}         → Get full kit details
DELETE /kits/{kit_id}       → Delete a kit
GET  /kits/{kit_id}/stream  → SSE progress stream
GET  /shared/{share_token}  → View shared kit (no auth)
```

#### Pipeline State Machine

```
                ┌──────────┐
                │ PENDING  │
                └────┬─────┘
                     │ run_pipeline()
                     ▼
                ┌──────────────┐
                │  GENERATING  │──── progress: 5% → 85%
                └──────┬───────┘
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ COMPLETE │ │ PARTIAL  │ │  FAILED  │
    │(all good)│ │(some fail)│ │(critical)│
    └──────────┘ └──────────┘ └──────────┘
```

#### Progress Tracking

| Step | Progress % | Description |
|------|-----------|-------------|
| parsing | 5% | Job started |
| parsing_resume_and_jd | 10% | Phase 1 (parallel) |
| match_analysis | 25% | Phase 2 |
| generating_kit_sections | 35% | Phase 3 starts |
| assembling | 85% | Phase 4 |
| complete | 100% | Done |

#### Requirements to Implement
- FastAPI + Uvicorn
- httpx (async HTTP client for service calls)
- asyncio (parallel execution)
- sse-starlette (Server-Sent Events)
- SQLAlchemy + asyncpg

#### Improvements Needed
1. **Task queue** — runs pipeline in-process; should use Celery/ARQ for reliability
2. **Retry failed generators** — no automatic retry on single generator failure
3. **Timeout per generator** — individual generator timeout (currently 60s global)
4. **Idempotency** — re-submitting same JD+resume creates duplicates
5. **Cancellation** — no way to cancel an in-progress generation
6. **Priority queue** — all jobs have equal priority (pro users should be faster)
7. **Webhook notifications** — no callback when generation completes
8. **Progress granularity** — progress jumps in chunks; should be smoother
9. **Kit versioning** — no re-generation or version history
10. **Concurrent limits** — no limit on simultaneous pipeline executions

---

### 4.6 Export Service (Port 8005)

**Purpose:** Generate downloadable PDFs and shareable links from completed kits.

#### Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **PDF Generation** | Render kit as branded PDF | WeasyPrint + Jinja2 template |
| **PDF Download** | Serve generated PDF files | File response |
| **Shareable Links** | Create public URLs for kits | UUID share tokens |
| **HTML Fallback** | If WeasyPrint unavailable, save as HTML | Graceful degradation |

#### API Routes

```
POST /pdf/{kit_id}       → Generate PDF (returns download URL)
GET  /download/{kit_id}  → Download PDF file
POST /share/{kit_id}     → Create shareable link (returns URL)
```

#### PDF Template Structure
- Jinja2 HTML template (`kit_pdf.html`)
- Renders all kit sections: match analysis, questions, test, rubric, red flags, flow
- WeasyPrint converts HTML → PDF with CSS styling

#### Requirements to Implement
- FastAPI + Uvicorn
- WeasyPrint — HTML-to-PDF rendering
- Jinja2 — template engine
- SQLAlchemy + asyncpg

#### Improvements Needed
1. **Cloud storage** — PDFs stored locally; should use S3/GCS
2. **PDF caching** — regenerates PDF on every request
3. **Template customization** — single template; users may want branding
4. **Export formats** — only PDF; add DOCX, Google Docs, Notion
5. **Batch export** — no multi-kit export
6. **Link expiration** — share links never expire; should have TTL option
7. **Access analytics** — no tracking of share link views
8. **Watermarking** — no free-tier watermark enforcement
9. **Async generation** — PDF generation is synchronous; could timeout on large kits
10. **File cleanup** — no cleanup of old generated PDFs

---

## 5. Frontend Application

### Tech Stack
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** Zustand
- **HTTP:** Axios with interceptors
- **Icons:** Lucide React
- **Notifications:** React Hot Toast

### Pages

#### 5.1 Landing Page (`/`)
- Hero section with product description
- CTAs: "Generate Kit" → `/generate`, "My Kits" → `/dashboard`
- No authentication required

#### 5.2 Login Page (`/login`)
- Email + password form
- Toggle between Login / Register modes
- Google OAuth button
- Stores JWT tokens in localStorage
- Redirects to `/dashboard` on success

#### 5.3 Generate Page (`/generate`)
- **Role Selector:** 8 role types (backend, frontend, fullstack, data_engineer, devops, ml_engineer, mobile, engineering_manager)
- **JD Input:** Large textarea for pasting job description
- **Resume Upload:** Drag-and-drop zone (PDF/DOCX, max 10MB) + text paste option
- **Submit:** Calls API, receives job_id, redirects to kit detail with SSE

#### 5.4 Dashboard (`/dashboard`)
- Lists user's kits with pagination
- Kit cards show: title, role_type, status badge, creation date
- Click → navigate to `/kit/[id]`
- Protected route (requires auth)

#### 5.5 Kit Detail (`/kit/[id]`)
- **Match Analysis Section:** Score gauge, skill matches (green), skill gaps (red)
- **Questions Section:** Expandable cards, difficulty badge, category tag, model answer, follow-ups
- **Practical Test Section:** 3 tabs (junior/mid/senior), task description, deliverables, evaluation criteria
- **Rubric Section:** Table with criteria, weights, score calibrations (1/3/5)
- **Red Flags Section:** Severity-colored alerts, probe questions, response indicators
- **Flow Guide Section:** Timeline visualization, section durations, mapped questions
- **Actions:** Export PDF, Share, Delete

### Components

| Component | Purpose |
|-----------|---------|
| `file-upload.tsx` | Drag-drop file upload with validation |
| `kit-viewer.tsx` | Full kit display with all sections |

### API Client (`api-client.ts`)
- Axios instance with base URL from env
- Request interceptor: attaches `Authorization: Bearer <token>`
- Response interceptor: on 401, redirects to `/login`
- Token stored in `localStorage`

### Requirements to Implement
- Node.js 18+
- next, react, react-dom
- axios, zustand
- tailwindcss, postcss, autoprefixer
- lucide-react, react-hot-toast
- typescript

### Improvements Needed
1. **Loading states** — minimal skeleton/loading UI during data fetch
2. **Error boundaries** — no React error boundary components
3. **Offline support** — no service worker or offline fallback
4. **Accessibility** — no ARIA labels, keyboard navigation untested
5. **SEO** — no meta tags, no sitemap, no structured data
6. **Token storage** — localStorage is vulnerable to XSS; use httpOnly cookies
7. **State persistence** — zustand store not persisted across refreshes
8. **Responsive design** — basic Tailwind but no mobile-specific layouts
9. **Testing** — no frontend unit/integration tests
10. **Dark mode** — no theme toggle
11. **Internationalization** — English only, no i18n framework
12. **Analytics** — no usage tracking (Mixpanel, Amplitude)
13. **PWA** — no Progressive Web App capabilities
14. **Real-time updates** — SSE handling could be more robust (reconnection)

---

## 6. Database Design

### Entity Relationship Diagram

```
┌──────────────────┐       ┌────────────────────────────────────┐
│      users       │       │              kits                   │
├──────────────────┤       ├────────────────────────────────────┤
│ id (PK, UUID)    │──┐    │ id (PK, UUID)                      │
│ email (unique)   │  │    │ user_id (FK → users.id)            │
│ password_hash    │  │    │ title                               │
│ name             │  │    │ role_type                           │
│ auth_provider    │  │    │ status (enum)                       │
│ plan             │  └───>│ jd_text                             │
│ kits_gen_month   │       │ resume_text                         │
│ created_at       │       │ structured_resume (JSONB)           │
│ updated_at       │       │ structured_jd (JSONB)               │
└──────────────────┘       │ match_analysis (JSONB)              │
                           │ questions (JSONB)                    │
                           │ practical_test (JSONB)               │
                           │ rubric (JSONB)                       │
                           │ red_flags (JSONB)                    │
                           │ flow_guide (JSONB)                   │
                           │ pdf_url                              │
                           │ share_token (unique)                 │
                           │ created_at                           │
                           │ updated_at                           │
                           └──────────────┬─────────────────────┘
                                          │
                           ┌──────────────┴─────────────────────┐
                           │        generation_jobs              │
                           ├────────────────────────────────────┤
                           │ id (PK, UUID)                       │
                           │ kit_id (FK → kits.id)               │
                           │ user_id                             │
                           │ status (enum)                       │
                           │ current_step                        │
                           │ progress_pct                        │
                           │ error_message                       │
                           │ started_at                          │
                           │ completed_at                        │
                           └────────────────────────────────────┘

┌────────────────────────────┐    ┌────────────────────────────┐
│      parsed_resumes        │    │         feedback           │
├────────────────────────────┤    ├────────────────────────────┤
│ id (PK, UUID)              │    │ id (PK, UUID)              │
│ file_hash (indexed)        │    │ kit_id (FK → kits.id)      │
│ raw_text                   │    │ user_id (FK → users.id)    │
│ structured_data (JSONB)    │    │ rating (1-5)               │
│ created_at                 │    │ comment                    │
└────────────────────────────┘    │ created_at                 │
                                  └────────────────────────────┘
```

### Indexes
- `users(email)` — unique, login lookup
- `kits(user_id)` — user's kit list
- `kits(status)` — filter by status
- `kits(created_at)` — sorting
- `kits(share_token)` — unique, public access
- `generation_jobs(kit_id)` — job lookup
- `generation_jobs(status)` — active jobs
- `parsed_resumes(file_hash)` — cache lookup

---

## 7. Shared Infrastructure

### 7.1 Authentication Module (`shared/auth/`)

```python
# Token creation
create_access_token(user_id: str) → str   # 15-min JWT
create_refresh_token(user_id: str) → str  # 7-day JWT

# Token verification
verify_token(token, secret_key, algorithm) → TokenData | None
```

### 7.2 Database Module (`shared/database/`)

```python
class DatabaseManager:
    """Async SQLAlchemy session manager with connection pooling."""
    async_session: AsyncSession factory
    
init_database() → DatabaseManager  # Initialize singleton
get_database() → DatabaseManager   # Retrieve singleton
```

### 7.3 Configuration (`shared/config/`)

All services inherit from `BaseAppSettings` (Pydantic BaseSettings):
- `app_name`, `app_env`, `debug`, `log_level`
- `database_url`, `redis_url`
- `jwt_secret_key`, `jwt_algorithm`, token expiry settings
- Service URLs (gateway, auth, resume, ai_engine, orchestrator, export)
- CORS origins
- Rate limit thresholds
- LLM API keys and model names

### 7.4 Schemas (`shared/schemas/`)

| File | Contents |
|------|----------|
| `auth.py` | UserCreate, UserResponse, TokenResponse, LoginRequest, GoogleOAuthRequest, TokenPayload |
| `resume.py` | StructuredResume, Project, Education, Employment, ResumeParseResponse |
| `kit.py` | RoleType, KitStatus, StructuredJD, Question, PracticalTest, PracticalTestVariant, Rubric, RubricCriterion, RedFlag, FlowSection, MatchAnalysis, KitGenerateRequest, KitResponse, KitListResponse, JobStatus |
| `common.py` | HealthResponse, ErrorResponse, PaginationParams |

---

## 8. Deployment & DevOps

### Docker Compose (Local Development)

```yaml
services:
  postgres:     # Port 5432
  redis:        # Port 6379
  gateway:      # Port 8000
  auth:         # Port 8001
  resume:       # Port 8002
  ai_engine:    # Port 8003
  orchestrator: # Port 8004
  export:       # Port 8005
```

### Makefile Commands

| Command | Action |
|---------|--------|
| `make setup` | Install dependencies, create data directories |
| `make run` | Start all 6 services locally (uvicorn) |
| `make run-docker` | Docker Compose up |
| `make test` | Run pytest suite |
| `make lint` | ruff check + format |
| `make migrate` | Run Alembic migrations |
| `make gateway` | Start only gateway service |
| `make auth` | Start only auth service |
| `make resume` | Start only resume service |
| `make ai-engine` | Start only AI engine |
| `make orchestrator` | Start only orchestrator |
| `make export` | Start only export service |

### Environment Variables (`.env`)

```
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/interviewkit

# Redis
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET_KEY=<random-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LLM_PRIMARY_MODEL=claude-3-5-sonnet-20241022
LLM_FALLBACK_MODEL=gpt-4-turbo-preview

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Service URLs (for inter-service communication)
AUTH_SERVICE_URL=http://localhost:8001
RESUME_SERVICE_URL=http://localhost:8002
AI_ENGINE_SERVICE_URL=http://localhost:8003
KIT_ORCHESTRATOR_SERVICE_URL=http://localhost:8004
EXPORT_SERVICE_URL=http://localhost:8005
```

### Production Deployment Strategy
- **Frontend:** Vercel (automatic from Git)
- **Backend:** Railway / Render (Docker containers)
- **Database:** Supabase PostgreSQL
- **Cache:** Redis Cloud / Upstash

---

## 9. Requirements & Dependencies

### Backend (Python)

```
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.6
python-dotenv>=1.0.0

# Database
sqlalchemy[asyncio]>=2.0.23
asyncpg>=0.29.0
alembic>=1.13.0

# Cache
redis>=5.0.0

# Authentication
pyjwt>=2.8.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.1.0
httpx>=0.25.0

# LLM Providers
anthropic>=0.7.0
openai>=1.3.0

# Resume Parsing
PyMuPDF>=1.23.0
python-docx>=1.0.0

# PDF Export
weasyprint>=60.0
jinja2>=3.1.2

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
ruff>=0.1.0
```

### Frontend (Node.js)

```json
{
  "next": "14.x",
  "react": "18.x",
  "typescript": "5.x",
  "axios": "^1.6",
  "zustand": "^4.4",
  "tailwindcss": "^3.3",
  "lucide-react": "^0.294",
  "react-hot-toast": "^2.4"
}
```

### Infrastructure
- PostgreSQL 15+
- Redis 7+
- Docker + Docker Compose
- Node.js 18+ (frontend)
- Python 3.11+ (backend)

---

## 10. Improvements & Recommendations

### 10.1 Architecture-Level Improvements

| Priority | Improvement | Impact |
|----------|-------------|--------|
| **HIGH** | Add message queue (RabbitMQ/Redis Streams) for pipeline | Reliability, scalability |
| **HIGH** | Implement circuit breakers between services | Fault tolerance |
| **HIGH** | Add distributed tracing (OpenTelemetry) | Observability |
| **HIGH** | Move to httpOnly cookies for JWT storage | Security |
| **MEDIUM** | Add API rate limiting per user (not just IP) | Fair usage |
| **MEDIUM** | Implement CQRS for kit reads vs writes | Performance |
| **MEDIUM** | Add health check dependencies (deep checks) | Reliability |
| **MEDIUM** | Service mesh or API gateway (Kong/Envoy) | Operations |
| **LOW** | Event sourcing for kit generation audit trail | Debugging |
| **LOW** | GraphQL gateway for flexible frontend queries | Developer experience |

### 10.2 Security Improvements

| Priority | Improvement | Current State |
|----------|-------------|---------------|
| **CRITICAL** | Move JWT from localStorage to httpOnly cookies | XSS vulnerable |
| **HIGH** | Add CSRF protection | Not implemented |
| **HIGH** | Input sanitization on JD/resume text | No XSS filtering |
| **HIGH** | File upload virus scanning | No malware check |
| **HIGH** | Rate limit login attempts | No brute-force protection |
| **MEDIUM** | Implement token refresh rotation | No rotation |
| **MEDIUM** | Add audit logging | No security audit trail |
| **MEDIUM** | Content Security Policy headers | Not configured |
| **LOW** | Implement MFA/2FA | Email-only auth |

### 10.3 Performance Improvements

| Priority | Improvement | Expected Gain |
|----------|-------------|---------------|
| **HIGH** | Cache LLM responses for identical inputs | 50%+ cost reduction |
| **HIGH** | Implement connection pooling properly | Reduce DB connection overhead |
| **MEDIUM** | Add Redis caching for kit reads | <50ms reads |
| **MEDIUM** | Implement CDN for PDF downloads | Faster downloads |
| **MEDIUM** | Use streaming LLM responses | Better perceived performance |
| **LOW** | Database read replicas | Scale reads |

### 10.4 Feature Improvements

| Priority | Feature | Description |
|----------|---------|-------------|
| **HIGH** | Email verification | Confirm user email on registration |
| **HIGH** | Password reset flow | Forgot password with email link |
| **HIGH** | Kit re-generation | Allow regenerating specific sections |
| **MEDIUM** | Team workspaces | Share kits within organization |
| **MEDIUM** | Candidate comparison | Side-by-side kit comparison |
| **MEDIUM** | Interview debrief forms | Post-interview scoring templates |
| **MEDIUM** | Custom question injection | Add interviewer's own questions |
| **LOW** | ATS integration | Import JDs from Greenhouse/Lever |
| **LOW** | Calendar integration | Schedule interviews from the kit |
| **LOW** | Public API | Third-party integrations |

### 10.5 Code Quality Improvements

| Priority | Improvement | Current State |
|----------|-------------|---------------|
| **HIGH** | Add comprehensive test suite | Tests folder exists but minimal |
| **HIGH** | Structured error responses | Inconsistent error formats |
| **HIGH** | Centralized logging (ELK/Datadog) | print statements only |
| **MEDIUM** | API documentation (OpenAPI/Swagger) | FastAPI auto-generates but no examples |
| **MEDIUM** | Database migrations (Alembic) | init_db.sql only, no migration history |
| **MEDIUM** | CI/CD pipeline | No GitHub Actions configured |
| **LOW** | Code coverage reporting | No coverage thresholds |
| **LOW** | Load testing | No performance benchmarks |

### 10.6 Cost & Scaling Considerations

| Concern | Mitigation |
|---------|-----------|
| LLM API costs ($0.01-0.10/kit) | Cache, prompt optimization, cheaper models for simple tasks |
| Database connections | Connection pooling, read replicas |
| Concurrent generation | Task queue with worker pool |
| PDF storage growth | S3 lifecycle policies, TTL-based cleanup |
| Redis memory | Key expiration, eviction policies |

---

## 11. Flowcharts

### 11.1 Complete System Flow

```mermaid
flowchart TD
    A[User visits app] --> B{Authenticated?}
    B -->|No| C[Login/Register Page]
    C --> D{Auth Method}
    D -->|Email| E[POST /auth/register or /login]
    D -->|Google| F[POST /auth/oauth/google]
    E --> G[Receive JWT Tokens]
    F --> G
    G --> H[Store tokens in localStorage]
    
    B -->|Yes| I[Dashboard - View Kits]
    H --> I
    
    I --> J[Click 'Generate New Kit']
    J --> K[Generate Page]
    
    K --> L[Select Role Type]
    L --> M[Paste Job Description]
    M --> N[Upload Resume / Paste Text]
    N --> O[Click Generate]
    
    O --> P[POST /api/v1/kits/generate]
    P --> Q[Gateway: Auth + Rate Limit]
    Q --> R[Kit Orchestrator: Create Job]
    R --> S[Return job_id + kit_id]
    
    S --> T[Frontend: Connect SSE Stream]
    T --> U[Watch Progress Updates]
    
    R --> V[Background Pipeline]
    V --> W[Phase 1: Parse Resume + Analyze JD]
    W --> X[Phase 2: Match Score]
    X --> Y[Phase 3: Generate All Sections]
    Y --> Z[Phase 4: Assemble Kit]
    Z --> AA[Update DB: Status = Complete]
    
    AA --> AB[SSE: Send 'complete' event]
    AB --> AC[Frontend: Load Kit Detail]
    
    AC --> AD[View Full Interview Kit]
    AD --> AE{User Action}
    AE -->|Export| AF[POST /export/pdf - Download PDF]
    AE -->|Share| AG[POST /export/share - Get Link]
    AE -->|Delete| AH[DELETE /kits/{id}]
    AE -->|New Kit| J
```

### 11.2 Pipeline Execution Flow

```mermaid
flowchart LR
    subgraph "Phase 1 (Parallel)"
        A1[Resume Service<br/>POST /parse] 
        A2[AI Engine<br/>POST /analyze-jd]
    end
    
    subgraph "Phase 2"
        B1[AI Engine<br/>POST /match-score]
    end
    
    subgraph "Phase 3 (Parallel)"
        C1[Generate Questions]
        C2[Generate Test]
        C3[Generate Rubric]
        C4[Generate Red Flags]
        C5[Generate Flow Guide]
    end
    
    subgraph "Phase 4"
        D1[Assemble Kit<br/>Store in DB]
    end
    
    A1 --> B1
    A2 --> B1
    B1 --> C1
    B1 --> C2
    B1 --> C3
    B1 --> C4
    B1 --> C5
    C1 --> D1
    C2 --> D1
    C3 --> D1
    C4 --> D1
    C5 --> D1
```

### 11.3 Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant GW as Gateway
    participant Auth as Auth Service
    participant DB as PostgreSQL

    U->>FE: Enter email + password
    FE->>GW: POST /api/v1/auth/login
    GW->>Auth: Forward request
    Auth->>DB: SELECT user by email
    DB-->>Auth: User record
    Auth->>Auth: Verify bcrypt hash
    Auth->>Auth: Generate JWT (access + refresh)
    Auth-->>GW: {access_token, refresh_token}
    GW-->>FE: 200 OK + tokens
    FE->>FE: Store in localStorage
    FE-->>U: Redirect to /dashboard
    
    Note over FE,GW: Subsequent requests
    FE->>GW: GET /kits (Authorization: Bearer <token>)
    GW->>GW: Verify JWT signature + expiry
    GW->>Auth: Forward (user context attached)
```

### 11.4 Kit Generation Detail

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant GW as Gateway
    participant KO as Kit Orchestrator
    participant RS as Resume Service
    participant AI as AI Engine
    participant DB as PostgreSQL

    FE->>GW: POST /kits/generate {jd, resume, role_type}
    GW->>KO: Forward (authenticated)
    KO->>DB: INSERT kit (status=pending)
    KO->>DB: INSERT generation_job (status=pending)
    KO-->>FE: {job_id, kit_id}
    
    FE->>GW: GET /kits/{id}/stream (SSE)
    
    Note over KO: Background async task starts
    
    par Phase 1 (Parallel)
        KO->>RS: POST /parse (resume file/text)
        RS-->>KO: StructuredResume
    and
        KO->>AI: POST /analyze-jd (jd_text)
        AI-->>KO: StructuredJD
    end
    
    KO->>AI: POST /match-score (resume + jd)
    AI-->>KO: MatchAnalysis {score: 78%}
    
    par Phase 3 (5 Parallel Generators)
        KO->>AI: POST /generate-questions
        AI-->>KO: 10 Questions
    and
        KO->>AI: POST /generate-test
        AI-->>KO: PracticalTest (3 variants)
    and
        KO->>AI: POST /generate-rubric
        AI-->>KO: Rubric (8 criteria)
    and
        KO->>AI: POST /generate-red-flags
        AI-->>KO: 3-5 RedFlags
    and
        KO->>AI: POST /generate-flow
        AI-->>KO: FlowGuide (5 sections)
    end
    
    KO->>DB: UPDATE kit (all sections, status=complete)
    KO->>DB: UPDATE job (status=complete, progress=100%)
    KO-->>FE: SSE event: {status: "complete"}
    FE->>GW: GET /kits/{id}
    GW->>KO: Forward
    KO->>DB: SELECT kit
    KO-->>FE: Full kit JSON
```

### 11.5 Export & Sharing Flow

```mermaid
flowchart TD
    A[User clicks 'Export PDF'] --> B[POST /api/v1/export/pdf/{kit_id}]
    B --> C[Export Service]
    C --> D[Fetch kit from DB]
    D --> E[Load Jinja2 template]
    E --> F[Render HTML with kit data]
    F --> G[WeasyPrint: HTML → PDF]
    G --> H[Save PDF to disk]
    H --> I[Return download URL]
    I --> J[User downloads PDF]
    
    K[User clicks 'Share'] --> L[POST /api/v1/export/share/{kit_id}]
    L --> M[Export Service]
    M --> N[Generate UUID share_token]
    N --> O[Store token in kit record]
    O --> P[Return share URL]
    P --> Q[User copies/shares link]
    Q --> R[Recipient visits link]
    R --> S[GET /shared/{share_token}]
    S --> T[View kit without auth]
```

---

## Summary of All Capabilities

| # | Capability | Status |
|---|-----------|--------|
| 1 | User registration (email + password) | ✅ Implemented |
| 2 | User login with JWT tokens | ✅ Implemented |
| 3 | Google OAuth authentication | ✅ Implemented |
| 4 | PDF resume upload and parsing | ✅ Implemented |
| 5 | DOCX resume upload and parsing | ✅ Implemented |
| 6 | Raw text resume input | ✅ Implemented |
| 7 | LLM-powered resume structuring | ✅ Implemented |
| 8 | Resume parse caching (file hash) | ✅ Implemented |
| 9 | Job description analysis | ✅ Implemented |
| 10 | Resume-JD match scoring (0-100%) | ✅ Implemented |
| 11 | Tailored question generation (10 questions) | ✅ Implemented |
| 12 | Practical test generation (3 variants) | ✅ Implemented |
| 13 | Scoring rubric generation (8 criteria) | ✅ Implemented |
| 14 | Red flags identification + probes | ✅ Implemented |
| 15 | Interview flow guide (60 min) | ✅ Implemented |
| 16 | Parallel pipeline execution | ✅ Implemented |
| 17 | SSE real-time progress streaming | ✅ Implemented |
| 18 | Partial success handling | ✅ Implemented |
| 19 | LLM fallback (Claude → GPT-4) | ✅ Implemented |
| 20 | Kit CRUD operations | ✅ Implemented |
| 21 | Kit pagination & listing | ✅ Implemented |
| 22 | PDF export with branded template | ✅ Implemented |
| 23 | Shareable kit links | ✅ Implemented |
| 24 | Redis rate limiting (fail-open) | ✅ Implemented |
| 25 | Free tier enforcement (3 kits/month) | ✅ Implemented |
| 26 | Multi-role support (8 role types) | ✅ Implemented |
| 27 | Docker Compose deployment | ✅ Implemented |
| 28 | Responsive frontend (Tailwind) | ✅ Implemented |
| 29 | Drag-drop file upload | ✅ Implemented |
| 30 | Kit deletion | ✅ Implemented |
| 31 | Email verification | ❌ Not implemented |
| 32 | Password reset | ❌ Not implemented |
| 33 | Refresh token rotation | ❌ Not implemented |
| 34 | Team workspaces | ❌ Not implemented |
| 35 | Candidate comparison | ❌ Not implemented |
| 36 | Stripe billing | ❌ Not implemented |
| 37 | ATS integrations | ❌ Not implemented |
| 38 | CI/CD pipeline | ❌ Not implemented |
| 39 | Comprehensive test suite | ❌ Not implemented |
| 40 | Production monitoring/alerting | ❌ Not implemented |

---

*Document generated: May 2026*
*Repository: ai_interviewer*
*Architecture: 6 Microservices + Next.js Frontend*
