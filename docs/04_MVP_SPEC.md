# InterviewKit AI — MVP Specification

## What is the MVP?

The MVP is **Phase 0 + Phase 1** (8 weeks). It delivers:

> **A user uploads a Job Description + Resume → receives a complete, personalized interview kit in under 25 seconds.**

The kit contains:
1. 8-12 tailored interview questions with model answers
2. A personalized practical assessment (3 difficulty levels)
3. A weighted scoring rubric with calibration examples
4. 3-5 candidate red flags with probe questions
5. A minute-by-minute interview flow guide
6. One-click PDF export

---

## MVP Scope (IN)

| Feature | Status |
|---------|--------|
| JD + Resume input (paste + upload) | ✅ IN |
| Role type selector (5 data roles) | ✅ IN |
| AI question generation + model answers | ✅ IN |
| Practical test generation (3 variants) | ✅ IN |
| Scoring rubric generation | ✅ IN |
| Red flags + probes | ✅ IN |
| Interview flow guide | ✅ IN |
| PDF export | ✅ IN |
| User auth (email + Google OAuth) | ✅ IN |
| Kit history dashboard | ✅ IN |
| Free tier (3 kits/month) | ✅ IN |
| Real-time generation progress (SSE) | ✅ IN |

---

## MVP Scope (OUT — Phase 2+)

| Feature | Phase |
|---------|-------|
| Candidate comparison | Phase 2 |
| Team workspaces | Phase 2 |
| Post-interview debrief | Phase 2 |
| Stripe billing (paid plans) | Phase 2 |
| ATS integrations | Phase 3 |
| Calendar integration | Phase 3 |
| Public API | Phase 3 |
| SEO pages | Phase 3 |
| Bias detection | Phase 4 |
| ML-driven prompt quality | Phase 4 |

---

## MVP User Flow

```
1. User lands on homepage → clicks "Generate Kit"
2. Paste/upload JD (left panel) + Resume (right panel)
3. Select role type (Data Scientist / ML Engineer / Data Analyst / Data Engineer / Analytics Engineer)
4. Click "Generate Interview Kit"
5. Progress bar streams status: "Parsing resume..." → "Analyzing JD..." → "Generating questions..." → etc.
6. Kit appears section by section (streaming reveal)
7. User reviews kit, expands question cards, views practical test variants
8. User clicks "Download PDF" → gets branded printable kit
9. Kit saved to dashboard for future reference
```

---

## MVP Technical Requirements

### Performance
- Total generation time: < 25 seconds
- Perceived time (with streaming): < 10 seconds
- Resume parsing: < 4 seconds
- PDF generation: < 5 seconds
- API response (non-AI): < 200ms

### Reliability
- 99.5% uptime (4.4 hours downtime/month acceptable for MVP)
- Graceful degradation if one AI section fails (show partial kit)
- LLM fallback: Claude → GPT-4

### Security
- HTTPS everywhere
- JWT auth with refresh tokens
- File upload validation (type, size < 10MB)
- No PII in logs
- Resume data encrypted at rest

### Scale (MVP target)
- 100 concurrent users
- 1,000 kits generated per day
- < 500ms p99 for non-AI endpoints

---

## MVP Database Schema

```sql
-- Core tables for MVP

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- null for OAuth users
    name VARCHAR(255),
    auth_provider VARCHAR(50) DEFAULT 'email',  -- email, google
    plan VARCHAR(20) DEFAULT 'free',  -- free, pro
    kits_generated_this_month INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),  -- auto-generated from JD role
    role_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'generating',  -- generating, complete, failed
    jd_text TEXT NOT NULL,
    resume_text TEXT,
    resume_file_url VARCHAR(500),
    structured_resume JSONB,
    structured_jd JSONB,
    match_analysis JSONB,
    questions JSONB,       -- array of question objects
    practical_test JSONB,  -- test with 3 variants
    rubric JSONB,          -- criteria array
    red_flags JSONB,       -- flags array
    flow_guide JSONB,      -- time-slot array
    pdf_url VARCHAR(500),
    share_token UUID UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID REFERENCES kits(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, complete, failed
    current_step VARCHAR(50),
    progress_pct INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_kits_user_id ON kits(user_id);
CREATE INDEX idx_kits_created_at ON kits(created_at DESC);
CREATE INDEX idx_kits_share_token ON kits(share_token);
CREATE INDEX idx_jobs_kit_id ON generation_jobs(kit_id);
CREATE INDEX idx_jobs_status ON generation_jobs(status);
```

---

## MVP API Endpoints

### Auth
```
POST   /api/v1/auth/register        → { user, access_token }
POST   /api/v1/auth/login            → { user, access_token }
POST   /api/v1/auth/google           → { user, access_token }
POST   /api/v1/auth/refresh          → { access_token }
GET    /api/v1/auth/me               → { user }
```

### Kits
```
POST   /api/v1/kits/generate         → { job_id, kit_id }
GET    /api/v1/kits/:id              → { kit }
GET    /api/v1/kits                  → { kits[], total, page }
DELETE /api/v1/kits/:id              → { success }
GET    /api/v1/kits/:id/stream       → SSE (progress events)
```

### Export
```
POST   /api/v1/export/pdf/:kit_id    → { pdf_url }
GET    /api/v1/export/download/:id   → PDF file
POST   /api/v1/export/share/:kit_id  → { share_url }
GET    /api/v1/shared/:token         → { kit } (public, no auth)
```

---

## MVP Cost Estimate

| Item | Monthly Cost |
|------|-------------|
| Vercel (frontend) | $0 (hobby) → $20 (pro) |
| Railway (5 services) | $25–$100 |
| Supabase (DB + auth + storage) | $0 (free tier) |
| Redis (Upstash) | $0 (free tier) |
| Claude API (~1000 kits @ $0.15/kit) | $150 |
| Domain | ~$1.25/mo |
| **Total MVP** | **$175–$275/month** |

Break-even at **5–7 paying users** ($39/month Pro plan).

---

## MVP Launch Checklist

- [ ] All 6 services running in production
- [ ] Auth working (email + Google)
- [ ] Full kit generation pipeline working end-to-end
- [ ] PDF export generating clean, branded documents
- [ ] Free tier limits enforced (3 kits/month)
- [ ] Error handling: partial failures show partial kit
- [ ] Mobile-responsive UI
- [ ] Landing page updated with "Try it now" CTA
- [ ] Sentry error tracking active
- [ ] PostHog analytics tracking key events
- [ ] Load tested: 100 concurrent kit generations
- [ ] Security review: no secrets exposed, inputs validated
- [ ] README + API docs in repo
