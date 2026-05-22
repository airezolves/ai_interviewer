# InterviewKit AI — End-to-End Roadmap

## Product Vision

**One-liner:** AI generates complete, personalized interview kits for technical hiring in 60 seconds.

**Core loop:** Hiring Manager pastes JD + uploads resume → AI generates tailored questions, practical test, scoring rubric, red flags, and interview flow guide → Manager downloads kit or uses in-app → After interview, fills debrief → Compares candidates.

---

## Phase 0: Foundation & Validation (Week 1–2)

### Goal
Prove demand exists before writing product code. Validate prompt quality.

### Deliverables

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 0.1 | Landing page + waitlist (email capture, sample output) | FE1 | 2-3 days | P0 |
| 0.2 | Core LLM prompt R&D (question gen, test gen, rubric gen) | DS2 | 5-7 days | P0 |
| 0.3 | Resume parsing pipeline (PDF/DOCX → structured JSON) | DS1 | 3-4 days | P0 |
| 0.4 | Set up monorepo structure + Docker Compose | DS1 | 1 day | P0 |
| 0.5 | Set up CI/CD pipeline (GitHub Actions) | DS1 | 1 day | P1 |

### Success Metrics
- 200+ waitlist sign-ups in 2 weeks
- Prompt output quality validated on 10+ real resumes
- Resume parser handles 95%+ of PDF formats correctly

### Exit Criteria
- Waitlist active and capturing emails
- Prompt templates produce interview-quality output consistently
- Resume parsing works for PDF and DOCX

---

## Phase 1: Core MVP — The Interview Kit Engine (Week 3–8)

### Goal
Ship the core product: JD + Resume → complete interview kit in 60 seconds.

### Sprint 1 (Week 3-4): Core Backend Services

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 1.1 | Resume Service: API endpoints, PDF/DOCX parsing, LLM structuring | DS1 | 4 days | P0 |
| 1.2 | AI Engine Service: JD analyzer, question generator, model answers | DS2 | 5 days | P0 |
| 1.3 | AI Engine Service: Practical test generator (3 difficulty variants) | DS2 | 5 days | P0 |
| 1.4 | API Gateway: routing, rate limiting, request validation | DS1 | 3 days | P0 |
| 1.5 | Frontend: JD + Resume input UI (upload, paste, role selector) | FE1 | 4 days | P0 |

### Sprint 2 (Week 5-6): Pipeline & More Generators

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 2.1 | AI Engine: Rubric generator, red flags analyzer, flow guide | DS2 | 5 days | P0 |
| 2.2 | Kit Orchestrator: Pipeline controller, parallel execution | DS1 | 5 days | P0 |
| 2.3 | Kit Orchestrator: SSE streaming to frontend | DS1 | 2 days | P0 |
| 2.4 | Frontend: Kit display UI (cards, sections, streaming progress) | FE1 | 5 days | P0 |
| 2.5 | Frontend: Real-time generation progress indicator | FE1 | 2 days | P0 |

### Sprint 3 (Week 7-8): Auth, Export, Polish

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 3.1 | Auth Service: Email + Google OAuth, JWT, session management | DS1 | 4 days | P0 |
| 3.2 | Export Service: PDF generation (branded template) | DS1 | 3 days | P0 |
| 3.3 | Frontend: Auth UI (login, signup, dashboard, kit history) | FE1 | 4 days | P0 |
| 3.4 | Frontend: PDF download, kit sharing | FE1 | 2 days | P0 |
| 3.5 | Free tier + usage limits (3 kits/month free) | DS1 | 2 days | P0 |
| 3.6 | AI Engine: Prompt refinement based on internal testing | DS2 | 5 days | P0 |
| 3.7 | Integration testing: full pipeline end-to-end | ALL | 2 days | P0 |

### Success Metrics
- 100 users generate 300+ kits
- 30%+ users return for a second kit
- Average generation time < 25 seconds
- Kit quality rated 4+/5 by test users

### Exit Criteria
- Full pipeline works: upload → generate → view → download PDF
- Auth + free tier enforced
- Deployed to production (Vercel + Railway)

---

## Phase 2: Retention & Team Features (Week 9–16)

### Goal
Make the product sticky and unlock team-level revenue.

### Sprint 4-5 (Week 9-12)

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 4.1 | Candidate comparison dashboard (side-by-side, radar chart) | DS2 | 5 days | P1 |
| 4.2 | Post-interview debrief template (rubric-based scoring form) | DS1 | 4 days | P1 |
| 4.3 | Shareable kit links (UUID-based public routes) | DS1 | 2 days | P1 |
| 4.4 | Feedback loop system (post-interview quality ratings) | DS2 | 3 days | P1 |
| 4.5 | Frontend: Comparison UI, debrief form, share flow | FE1 | 7 days | P1 |

### Sprint 6-7 (Week 13-16)

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 5.1 | Team workspaces (invite, shared pool, RLS) | DS1 | 5 days | P2 |
| 5.2 | Role template library (15-20 role templates) | DS2 | 5 days | P2 |
| 5.3 | Stripe billing integration (monthly/annual, team billing) | DS1 | 4 days | P1 |
| 5.4 | Frontend: Team workspace UI, billing portal | FE1 | 5 days | P2 |
| 5.5 | Prompt quality analysis (aggregate feedback data) | DS2 | 3 days | P1 |

### Success Metrics
- 50 paying teams
- 30% monthly retention
- NPS > 40
- Team conversion rate > 15%

---

## Phase 3: Growth & Integrations (Month 5–8)

### Goal
Scale acquisition through SEO, integrations, and API. Target: $10K MRR.

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 6.1 | SEO interview question generator pages (50+ roles) | FE1 | 7-10 days | P1 |
| 6.2 | ATS integration: Greenhouse + Lever (OAuth, webhooks) | DS1 | 10-14 days | P2 |
| 6.3 | Calendar integration (Google + Outlook, auto-prompt) | DS1 | 5-7 days | P2 |
| 6.4 | Public API for embedding (REST, API keys, rate limits) | DS1 | 5-7 days | P2 |
| 6.5 | Stripe full billing + plan management | DS1 | 3-5 days | P1 |
| 6.6 | Internal analytics dashboard | DS2 | 3-4 days | P2 |
| 6.7 | Frontend: SEO pages, integration UIs, API docs | FE1 | 10 days | P1 |

### Success Metrics
- $10K+ MRR
- 500+ organic sign-ups/month from SEO
- 1 ATS integration live in marketplace

---

## Phase 4: Intelligence & Scale (Month 9–14)

### Goal
Build data moats and advanced features. Target: $30K MRR.

| # | Task | Owner | Effort | Priority |
|---|------|-------|--------|----------|
| 7.1 | Prompt quality engine (ML-driven A/B testing) | DS2 | 10-14 days | P1 |
| 7.2 | Interviewer performance analytics | DS2 | 7-10 days | P2 |
| 7.3 | Custom assessment builder | DS1 | 7-10 days | P2 |
| 7.4 | Multi-round interview planning | DS1 | 5-7 days | P2 |
| 7.5 | Bias detection & DEI reporting | DS2 | 5-7 days | P2 |
| 7.6 | Frontend: Advanced analytics, builder UIs, DEI reports | FE1 | 14 days | P2 |

### Success Metrics
- $30K+ MRR
- Data moat established (10K+ kits with feedback)
- Measurable prompt quality improvement from ML pipeline

---

## Timeline Summary

```
Week 1-2    ████ Phase 0: Foundation & Validation
Week 3-8    ████████████████████████ Phase 1: Core MVP
Week 9-16   ████████████████████████████████ Phase 2: Retention & Teams
Month 5-8   ████████████████████████████████████████ Phase 3: Growth
Month 9-14  ████████████████████████████████████████████████ Phase 4: Intelligence
```

---

## Key Decision Points

| After Phase | Decision |
|-------------|----------|
| Phase 0 | If <50 waitlist sign-ups → pivot messaging, not product |
| Phase 1 | If <30% return rate → kit quality needs work, delay Phase 2 |
| Phase 2 | If <10 paying teams → pricing/positioning problem, not feature problem |
| Phase 3 | If <$5K MRR → distribution is failing, double down on SEO + partnerships |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt quality feels "ChatGPT-level" | Fatal | Invest heavily in Phase 0 prompt R&D. Role-specific templates, not generic. |
| LLM rate limits during spikes | High | Queue + retry + fallback provider (Claude → GPT-4) |
| Resume parsing edge cases | Medium | LLM handles messy text. Fallback: user pastes text manually. |
| Solo burnout (now mitigated by team) | Medium | Clear task division. Sprints, not marathons. Ship weekly. |
| ATS adds basic AI questions | Medium | Practical tests are the moat. ATS won't replicate personalized assessments. |
| Scope creep into Phase 3 during Phase 1 | High | Strict phase gates. Do NOT build Phase 3 features until Phase 1 metrics are hit. |

---

## Pricing Strategy (Phase 1 launch)

| Plan | Price | Includes |
|------|-------|----------|
| Free | $0 | 3 kits/month, no practical test, no PDF export |
| Pro | $39/month | Unlimited kits, all features, PDF export |
| Team | $29/user/month (min 3) | Shared workspace, candidate comparison, team debrief |
| API | $0.50/kit | For B2B integrations (Phase 3) |
