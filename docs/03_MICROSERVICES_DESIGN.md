# InterviewKit AI — Microservices Design Document

## Service Independence Principles

1. **Each service owns its domain logic** — no cross-service function imports
2. **Communication via HTTP/REST or Redis queues** — never direct DB access across services
3. **Shared library for infrastructure only** — DB connector, config loader, base schemas
4. **Each service has its own config** — extends base config with service-specific settings
5. **Independent testability** — each service has unit + integration tests runnable in isolation
6. **Graceful degradation** — if PDF service is down, kit generation still works

---

## Service Contracts (API Specifications)

### Auth Service API

```
POST   /auth/register          → Register new user
POST   /auth/login             → Login (returns JWT)
POST   /auth/refresh           → Refresh JWT token
POST   /auth/logout            → Invalidate session
GET    /auth/me                → Get current user profile
PUT    /auth/me                → Update profile
POST   /auth/forgot-password   → Initiate password reset
POST   /auth/reset-password    → Complete password reset
POST   /auth/oauth/google      → Google OAuth callback
GET    /auth/validate-token    → Validate JWT (internal)
```

### Resume Parser Service API

```
POST   /resume/parse           → Upload + parse resume (returns structured JSON)
GET    /resume/{id}            → Get parsed resume by ID
GET    /resume/user/{user_id}  → List user's resumes
DELETE /resume/{id}            → Delete a resume
```

### AI Engine Service API

```
POST   /ai/analyze-jd          → Analyze job description → structured JSON
POST   /ai/generate-questions  → Generate interview questions + model answers
POST   /ai/generate-assessment → Generate practical assessment
POST   /ai/generate-rubric     → Generate scoring rubric
POST   /ai/generate-red-flags  → Identify candidate red flags
POST   /ai/generate-flow-guide → Generate interview flow guide
POST   /ai/generate-kit-full   → Full parallel kit generation (all sections)
GET    /ai/prompts/{role_type} → Get prompt templates for a role
GET    /ai/health              → Service health + LLM API status
```

### Kit Manager Service API

```
POST   /kits                    → Create new kit (triggers generation pipeline)
GET    /kits                    → List user's kits (paginated, filterable)
GET    /kits/{id}               → Get full kit with all sections
PUT    /kits/{id}               → Update kit metadata
DELETE /kits/{id}               → Delete a kit
GET    /kits/{id}/status        → Get generation status (polling endpoint)
POST   /kits/{id}/share         → Generate shareable link
GET    /kits/shared/{token}     → Access shared kit (public)
POST   /kits/{id}/feedback      → Submit feedback on a kit
GET    /kits/compare            → Compare multiple candidates for same role
```

### PDF Generator Service API

```
POST   /pdf/generate            → Generate PDF from kit data (async, returns job_id)
GET    /pdf/{job_id}/status     → Check PDF generation status
GET    /pdf/{job_id}/download   → Download generated PDF
DELETE /pdf/{job_id}            → Delete generated PDF
```

### Billing Service API

```
GET    /billing/plans           → List available plans
GET    /billing/subscription    → Get current user's subscription
POST   /billing/checkout        → Create Stripe checkout session
POST   /billing/portal          → Create Stripe customer portal session
GET    /billing/usage           → Get usage stats for current billing period
POST   /billing/webhooks/stripe → Stripe webhook handler
```

---

## Concurrency & Parallel Execution

### Kit Generation Pipeline (Parallel Execution)

```python
async def generate_full_kit(jd_text, resume_data, role_type):
    # Step 1: Sequential pre-processing
    jd_analysis = await ai_engine.analyze_jd(jd_text)
    match_context = build_match_context(jd_analysis, resume_data)
    
    # Step 2: Parallel generation (all independent)
    questions, assessment, rubric, red_flags, flow_guide = await asyncio.gather(
        ai_engine.generate_questions(match_context, role_type),
        ai_engine.generate_assessment(match_context, role_type),
        ai_engine.generate_rubric(match_context, role_type),
        ai_engine.generate_red_flags(resume_data, jd_analysis),
        ai_engine.generate_flow_guide(match_context, role_type),
    )
    
    # Step 3: Assembly
    return assemble_kit(questions, assessment, rubric, red_flags, flow_guide)
```

### Service-Level Concurrency

| Service | Concurrency Model | Workers |
|---------|-------------------|---------|
| Gateway | asyncio (uvicorn) | 4 workers |
| Auth | asyncio (uvicorn) | 2 workers |
| Resume Parser | asyncio + thread pool for file I/O | 2 workers |
| AI Engine | asyncio (parallel LLM calls) | 4 workers |
| Kit Manager | asyncio + background tasks | 2 workers |
| PDF Generator | asyncio + process pool for rendering | 2 workers |
| Billing | asyncio (uvicorn) | 1 worker |

---

## Error Handling & Resilience

### Retry Strategy
- LLM API calls: 3 retries with exponential backoff (2s, 4s, 8s)
- Inter-service calls: 2 retries with 1s backoff
- PDF generation: 2 retries, then mark as failed

### Circuit Breaker Pattern
- If AI Engine returns 5 consecutive 500s → circuit opens for 30s
- Gateway returns 503 to client with "generation temporarily unavailable"
- Circuit half-opens after 30s → single test request → full open if success

### Graceful Degradation
- If PDF service is down → kit still generated, PDF available later
- If Redis is down → fall back to synchronous processing (slower but functional)
- If billing service is down → allow generation (reconcile usage later)

---

## Security Model

### Authentication Flow
```
1. User logs in → Auth Service issues JWT (15min) + Refresh Token (7d)
2. All requests carry JWT in Authorization header
3. Gateway validates JWT signature (shared secret with Auth)
4. Gateway passes user_id to downstream services via X-User-ID header
5. Internal service-to-service calls use X-Service-Key header
```

### Data Protection
- Passwords: bcrypt hashed (12 rounds)
- JWT: HS256 signed with rotating secret
- Resume data: encrypted at rest in PostgreSQL
- File uploads: stored with user-scoped access paths
- PII stripped from all log entries
- Auto-delete resume files after 90 days

---

## Monitoring & Observability

| Tool | Purpose |
|------|---------|
| Structured Logging (JSON) | Request tracing, error tracking |
| Health endpoints (/health) | Service liveness checks |
| Prometheus metrics | Request latency, error rates, queue depth |
| Sentry | Exception tracking and alerting |
| PostHog | Product analytics (user-facing) |

---

## Development Workflow

```bash
# Start all services locally
docker-compose up

# Start individual service for development
cd services/ai_engine && uvicorn app:app --reload --port 8003

# Run tests for a service
pytest services/auth/tests/

# Run all tests
pytest tests/

# Database migrations
alembic upgrade head
```
