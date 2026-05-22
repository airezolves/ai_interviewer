# InterviewKit AI — Service Design & Implementation Guide

## Service Design Principles

1. **Single Responsibility:** Each service does one thing well
2. **Loose Coupling:** Services know nothing about each other's internals
3. **Independent Deployment:** Any service can be deployed without touching others
4. **Failure Isolation:** One service crash doesn't cascade
5. **Shared Nothing:** No direct DB access across service boundaries

---

## Service 1: API Gateway

### Purpose
Single entry point for all client requests. Handles cross-cutting concerns.

### Responsibilities
- Route requests to appropriate internal services
- Validate JWT tokens (delegates to Auth Service)
- Enforce rate limits (per user, per plan tier)
- CORS configuration
- Request/response logging
- API versioning (`/api/v1/`, `/api/v2/`)

### Internal Structure
```
services/gateway/
├── app/
│   ├── main.py              # FastAPI app init, middleware
│   ├── config.py            # Service URLs, rate limit configs
│   ├── middleware/
│   │   ├── auth.py          # JWT verification middleware
│   │   ├── rate_limiter.py  # Redis-based rate limiting
│   │   └── logging.py       # Request/response logging
│   ├── routes/
│   │   ├── auth.py          # Proxy to Auth Service
│   │   ├── kits.py          # Proxy to Kit Orchestrator
│   │   └── export.py        # Proxy to Export Service
│   └── utils/
│       └── http_client.py   # httpx async client for internal calls
├── requirements.txt
├── Dockerfile
└── tests/
    ├── test_auth_middleware.py
    └── test_rate_limiter.py
```

### Key Dependencies
```
fastapi
uvicorn
httpx          # async HTTP client
redis          # rate limiting
pyjwt          # JWT verification
pydantic
```

### Rate Limiting Strategy
```python
# Redis key: rate:{user_id}:{endpoint}:{window}
# Free tier: 3 kits/month, 10 requests/minute
# Pro tier:  unlimited kits, 60 requests/minute
```

---

## Service 2: Auth Service

### Purpose
User identity, authentication, authorization, and billing.

### Responsibilities
- User registration (email + password)
- Google OAuth flow
- JWT token generation + refresh
- User profile management
- Usage tracking (kits per month)
- Plan management (free/pro)
- Stripe webhook handling (future)

### Internal Structure
```
services/auth/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── user.py          # SQLAlchemy User model
│   │   └── subscription.py  # Plan & usage tracking
│   ├── routes/
│   │   ├── register.py
│   │   ├── login.py
│   │   ├── oauth.py         # Google OAuth
│   │   ├── profile.py
│   │   └── usage.py         # Usage tracking endpoints
│   ├── services/
│   │   ├── auth_service.py  # Core auth logic
│   │   ├── token_service.py # JWT generation/validation
│   │   └── usage_service.py # Kit count tracking
│   └── utils/
│       ├── password.py      # bcrypt hashing
│       └── oauth_client.py  # Google OAuth client
├── requirements.txt
├── Dockerfile
└── tests/
```

### Key Endpoints
```
POST /register     → Create user, return JWT
POST /login        → Validate credentials, return JWT
POST /oauth/google → Exchange code for JWT
POST /refresh      → Refresh expired token
GET  /me           → Get current user profile
GET  /usage        → Get usage stats (kits this month)
POST /usage/increment → Increment kit count (called by Orchestrator)
```

---

## Service 3: Resume Service

### Purpose
Parse uploaded resumes into structured, machine-readable JSON.

### Responsibilities
- Accept PDF and DOCX file uploads
- Extract raw text from documents
- Send raw text to LLM for structuring
- Cache parsed results (same file → same output)
- File storage (upload to S3/Supabase Storage)

### Internal Structure
```
services/resume/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── parser/
│   │   ├── pdf_parser.py    # PyMuPDF extraction
│   │   ├── docx_parser.py   # python-docx extraction
│   │   └── llm_structurer.py # Raw text → structured JSON
│   ├── routes/
│   │   └── parse.py         # POST /parse endpoint
│   ├── services/
│   │   ├── parse_service.py # Orchestrates parsing pipeline
│   │   └── cache_service.py # Redis caching by file hash
│   └── utils/
│       ├── file_validator.py # Type, size, safety checks
│       └── hash.py          # SHA256 for cache keys
├── requirements.txt
├── Dockerfile
└── tests/
    ├── test_pdf_parser.py
    ├── test_docx_parser.py
    └── test_structurer.py
```

### Output Schema
```python
class StructuredResume(BaseModel):
    skills: list[str]                    # ["Python", "TensorFlow", "SQL"]
    experience_level: str                # "senior", "mid", "junior"
    years_of_experience: float           # 5.5
    tech_stack: list[str]                # ["Python", "AWS", "Docker"]
    projects: list[Project]              # Key projects with descriptions
    education: list[Education]           # Degrees, institutions
    employment_timeline: list[Employment] # Chronological work history
    gaps: list[str]                      # Identified gaps or concerns
    summary: str                         # 2-3 sentence summary
    raw_text: str                        # Original extracted text
```

### Caching Strategy
```
Key: resume:{sha256(file_bytes)}
TTL: 7 days
Hit rate target: 30%+ (same candidate reviewed by multiple interviewers)
```

---

## Service 4: AI Engine Service

### Purpose
All LLM interactions. The "brain" of the system.

### Responsibilities
- Manage versioned prompt templates
- JD analysis and structuring
- Interview question generation with model answers
- Practical test generation (3 difficulty levels)
- Scoring rubric generation
- Red flags detection
- Interview flow guide generation
- Resume-JD match scoring

### Internal Structure
```
services/ai_engine/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── base.py              # Base prompt class
│   │   ├── jd_analysis.py       # JD structuring prompts
│   │   ├── questions.py         # Question gen prompts
│   │   ├── practical_test.py    # Test gen prompts (per role)
│   │   ├── rubric.py            # Rubric gen prompts
│   │   ├── red_flags.py         # Red flags prompts
│   │   ├── flow_guide.py        # Flow guide prompts
│   │   └── templates/           # Role-specific template variants
│   │       ├── data_scientist.py
│   │       ├── ml_engineer.py
│   │       ├── data_analyst.py
│   │       ├── data_engineer.py
│   │       └── analytics_engineer.py
│   ├── generators/
│   │   ├── jd_analyzer.py       # JD → structured output
│   │   ├── question_generator.py
│   │   ├── test_generator.py
│   │   ├── rubric_generator.py
│   │   ├── red_flags_generator.py
│   │   ├── flow_generator.py
│   │   └── match_scorer.py
│   ├── routes/
│   │   ├── analyze.py           # JD analysis endpoints
│   │   ├── generate.py          # All generation endpoints
│   │   └── health.py
│   ├── services/
│   │   ├── llm_client.py        # Claude/GPT client abstraction
│   │   └── prompt_manager.py    # Prompt versioning + loading
│   └── utils/
│       ├── output_parser.py     # JSON extraction from LLM output
│       └── retry.py             # LLM call retry logic
├── requirements.txt
├── Dockerfile
└── tests/
    ├── test_generators/
    └── test_prompts/
```

### LLM Client Abstraction
```python
class LLMClient:
    """Unified interface for Claude + GPT-4 fallback."""
    
    async def generate(
        self,
        prompt: str,
        system: str,
        output_schema: type[BaseModel] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str | BaseModel:
        """Try Claude first, fall back to GPT-4 on failure."""
        try:
            return await self._call_claude(prompt, system, output_schema, temperature, max_tokens)
        except (RateLimitError, APIError):
            return await self._call_openai(prompt, system, output_schema, temperature, max_tokens)
```

### Prompt Versioning
```python
# Each prompt template has a version
# Allows A/B testing and rollback
PROMPT_VERSIONS = {
    "questions_v1": "...",
    "questions_v2": "...",  # New variant being tested
}

# Active version configured in environment
ACTIVE_PROMPTS = {
    "questions": os.getenv("PROMPT_QUESTIONS_VERSION", "questions_v1"),
}
```

---

## Service 5: Kit Orchestrator Service

### Purpose
Coordinates the full generation pipeline. The "conductor."

### Responsibilities
- Accept kit generation requests
- Orchestrate parallel calls to Resume Service + AI Engine
- Track generation progress
- Assemble final kit from all outputs
- Store completed kits in database
- Stream progress to frontend via SSE
- Handle partial failures gracefully

### Internal Structure
```
services/kit_orchestrator/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── pipeline/
│   │   ├── controller.py     # Main pipeline state machine
│   │   ├── executor.py       # Parallel async execution
│   │   ├── assembler.py      # Combine outputs into kit
│   │   └── steps.py          # Individual pipeline step definitions
│   ├── routes/
│   │   ├── generate.py       # POST /generate endpoint
│   │   ├── kits.py           # CRUD for stored kits
│   │   └── stream.py         # SSE streaming endpoint
│   ├── services/
│   │   ├── kit_service.py    # Kit CRUD operations
│   │   ├── job_service.py    # Job tracking
│   │   └── stream_service.py # SSE event publishing
│   └── clients/
│       ├── resume_client.py  # HTTP client → Resume Service
│       ├── ai_client.py      # HTTP client → AI Engine
│       └── auth_client.py    # HTTP client → Auth Service (usage)
├── requirements.txt
├── Dockerfile
└── tests/
    ├── test_pipeline.py
    └── test_assembler.py
```

### Pipeline State Machine
```
PENDING → PARSING → ANALYZING → GENERATING → ASSEMBLING → COMPLETE
                                                          → PARTIAL (some steps failed)
                                              → FAILED (critical failure)
```

### Parallel Execution
```python
async def generate_kit(context: MatchContext) -> Kit:
    """Run all generators in parallel."""
    results = await asyncio.gather(
        ai_client.generate_questions(context),
        ai_client.generate_test(context),
        ai_client.generate_rubric(context),
        ai_client.analyze_red_flags(context),
        ai_client.generate_flow(context),
        return_exceptions=True,  # Don't fail all if one fails
    )
    
    kit = assemble_kit(results, allow_partial=True)
    return kit
```

---

## Service 6: Export Service

### Purpose
Generate downloadable artifacts (PDF, shareable links).

### Responsibilities
- Render kit JSON to branded PDF
- HTML template rendering (Jinja2)
- Shareable link generation
- PDF caching (24h TTL)
- Async PDF generation queue

### Internal Structure
```
services/export/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── templates/
│   │   ├── kit_pdf.html      # Full kit PDF template
│   │   ├── components/       # Reusable template partials
│   │   └── styles.css        # PDF-specific styles
│   ├── routes/
│   │   ├── pdf.py            # PDF generation endpoints
│   │   └── share.py          # Shareable link endpoints
│   ├── services/
│   │   ├── pdf_service.py    # WeasyPrint rendering
│   │   ├── share_service.py  # UUID link management
│   │   └── cache_service.py  # Redis PDF cache
│   └── utils/
│       └── storage.py        # Upload PDF to S3/storage
├── requirements.txt
├── Dockerfile
└── tests/
    └── test_pdf_generation.py
```

---

## Shared Package

### Purpose
Common code used by multiple services (avoid duplication).

```
shared/
├── __init__.py
├── schemas/
│   ├── __init__.py
│   ├── resume.py        # StructuredResume, Education, Project, etc.
│   ├── jd.py            # StructuredJD, Skill, Requirement
│   ├── kit.py           # Kit, Question, PracticalTest, Rubric, etc.
│   ├── auth.py          # TokenPayload, UserBase
│   └── common.py        # Pagination, Error responses
├── auth/
│   ├── __init__.py
│   └── jwt_utils.py     # Token verification (used by Gateway)
├── config/
│   ├── __init__.py
│   └── base.py          # Base settings class (pydantic-settings)
└── setup.py             # Installable as `pip install -e shared/`
```

### Installation
Each service's Dockerfile installs the shared package:
```dockerfile
COPY shared/ /app/shared/
RUN pip install -e /app/shared/
```

---

## Docker Compose (Local Development)

```yaml
# infrastructure/docker-compose.yml
version: "3.8"

services:
  # --- Infrastructure ---
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: interviewkit
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # --- Application Services ---
  gateway:
    build: ../services/gateway
    ports:
      - "8000:8000"
    environment:
      - AUTH_SERVICE_URL=http://auth:8001
      - ORCHESTRATOR_URL=http://orchestrator:8004
      - EXPORT_SERVICE_URL=http://export:8005
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - auth
      - orchestrator
      - export

  auth:
    build: ../services/auth
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/interviewkit
      - JWT_SECRET=dev-secret-key
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    depends_on:
      - postgres

  resume:
    build: ../services/resume
    ports:
      - "8002:8002"
    environment:
      - REDIS_URL=redis://redis:6379
      - AI_ENGINE_URL=http://ai_engine:8003
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - redis
      - ai_engine

  ai_engine:
    build: ../services/ai_engine
    ports:
      - "8003:8003"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on: []

  orchestrator:
    build: ../services/kit_orchestrator
    ports:
      - "8004:8004"
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/interviewkit
      - REDIS_URL=redis://redis:6379
      - RESUME_SERVICE_URL=http://resume:8002
      - AI_ENGINE_URL=http://ai_engine:8003
      - AUTH_SERVICE_URL=http://auth:8001
    depends_on:
      - postgres
      - redis
      - resume
      - ai_engine

  export:
    build: ../services/export
    ports:
      - "8005:8005"
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/interviewkit
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # --- Frontend ---
  frontend:
    build: ../frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - gateway

volumes:
  pg_data:
```

---

## Health Check Pattern

Every service implements:
```python
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "service-name", "version": "0.1.0"}

@app.get("/health/ready")
async def readiness():
    """Check all dependencies are reachable."""
    checks = await check_dependencies()  # DB, Redis, etc.
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    raise HTTPException(503, {"status": "not ready", "checks": checks})
```

---

## Error Handling Pattern

Consistent error responses across all services:
```python
class ServiceError(BaseModel):
    error: str           # Machine-readable error code
    message: str         # Human-readable message
    details: dict | None # Additional context

# Example: 422
{
    "error": "RESUME_PARSE_FAILED",
    "message": "Could not extract text from the uploaded PDF",
    "details": {"filename": "resume.pdf", "reason": "encrypted PDF"}
}
```
