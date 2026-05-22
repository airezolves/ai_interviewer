# InterviewKit AI — Team Division & Sprint Plan

## Team Composition

| Role | ID | Focus Area | Tech Stack |
|------|----|-----------|------------|
| Data Science Backend 1 | **DS1** | Infrastructure, Resume Service, Kit Orchestrator, Auth, Export, Gateway | Python, FastAPI, PostgreSQL, Redis, Docker |
| Data Science Backend 2 | **DS2** | AI Engine, Prompt Engineering, LLM Orchestration, ML Pipeline | Python, FastAPI, Anthropic SDK, Prompt Design |
| Frontend Engineer | **FE1** | Full UI/UX, Next.js, API integration, real-time features | TypeScript, Next.js, Tailwind CSS, React |

---

## Service Ownership

```
┌─────────────────────────────────────────────────────────────────┐
│                        SERVICE OWNERSHIP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DS1 owns:                                                       │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ API Gateway │ │ Auth Service │ │Resume Service│             │
│  └─────────────┘ └──────────────┘ └──────────────┘             │
│  ┌──────────────────┐ ┌────────────────┐                        │
│  │ Kit Orchestrator │ │ Export Service │                        │
│  └──────────────────┘ └────────────────┘                        │
│                                                                  │
│  DS2 owns:                                                       │
│  ┌────────────────────────────────────────────┐                  │
│  │            AI Engine Service               │                  │
│  │  • Prompt Manager    • Question Generator  │                  │
│  │  • JD Analyzer       • Test Generator      │                  │
│  │  • Rubric Generator  • Red Flags Analyzer  │                  │
│  │  • Flow Guide Gen    • Match Scorer        │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                  │
│  FE1 owns:                                                       │
│  ┌────────────────────────────────────────────┐                  │
│  │            Frontend Service                │                  │
│  │  • Landing page      • Input UI           │                  │
│  │  • Kit display       • Auth UI            │                  │
│  │  • Dashboard         • PDF download       │                  │
│  │  • Team workspace    • SSE client         │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Foundation & Validation (Week 1–2)

### DS1 — Infrastructure & Resume Pipeline
| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Set up monorepo structure, Docker Compose, shared package | Working `docker-compose up` with all service stubs |
| 2 | Set up CI/CD (GitHub Actions: lint + test) | Green CI on push to main |
| 3-4 | Build Resume Service: PDF parsing (PyMuPDF) | `POST /parse` → raw text from any PDF |
| 5 | Build Resume Service: DOCX parsing (python-docx) | DOCX support complete |
| 6 | Resume Service: LLM structuring (feed raw text → structured JSON) | Full parse pipeline working |
| 7 | Integration: test with 10 real resumes, handle edge cases | 95%+ parse success rate |

### DS2 — Prompt Engineering & AI Core
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Design prompt architecture: templates, role specificity, output schemas | Prompt design doc + JSON schemas |
| 3-4 | Build & iterate: question generation prompts (data science roles) | 8-12 quality questions per JD+resume pair |
| 5-6 | Build & iterate: practical test generation prompts | Role-specific tests with 3 difficulty levels |
| 7-8 | Build & iterate: rubric generation + red flags prompts | Weighted rubric + probes output |
| 9-10 | Test with 10+ real resumes, refine quality, version prompts in Git | Quality benchmark: "clearly better than ChatGPT" |

### FE1 — Landing Page & Design System
| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Set up Next.js 14 project, Tailwind, TypeScript config | Working frontend dev environment |
| 2-3 | Build landing page (value prop, sample output, email capture) | Deployed landing page on Vercel |
| 4 | Integrate email capture (Resend/Mailchimp) | Working waitlist signup |
| 5-6 | Design system: component library (buttons, cards, forms, layout) | Reusable UI components |
| 7 | Design input UI mockup (JD + Resume panels) | Figma/code mockup approved |

---

## Phase 1, Sprint 1 (Week 3–4): Core Backend + Input UI

### DS1 — Resume Service API + Gateway
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Resume Service: full API (endpoints, validation, error handling) | Production-ready `/parse` endpoint |
| 3 | Resume Service: file upload to S3/Supabase Storage | File persistence working |
| 4 | Resume Service: caching (same file hash → cached result) | Redis cache layer |
| 5-6 | API Gateway: routing, CORS, request validation | Gateway routing to all services |
| 7-8 | API Gateway: rate limiting (per-user, per-plan) | Rate limits enforced |

### DS2 — AI Engine Service (JD + Questions)
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | AI Engine Service: project setup, prompt loader, config | Running service with health check |
| 3-4 | JD Analyzer endpoint: JD → structured JSON | `POST /analyze-jd` working |
| 5-7 | Question Generator endpoint: context → questions + model answers | `POST /generate-questions` working |
| 8-10 | Practical Test Generator endpoint: 3 difficulty variants | `POST /generate-test` working |

### FE1 — Input UI
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | JD input panel (paste text, upload file) | Working JD input with validation |
| 3-4 | Resume input panel (drag-drop PDF/DOCX, paste text) | Working resume upload |
| 5 | Role type selector (Data Scientist, ML Engineer, etc.) | Dropdown with 5 role types |
| 6-7 | File preview (show parsed text in UI) | Client-side preview |
| 8 | Connect to Gateway API (submit JD + resume) | End-to-end: upload → API call |

---

## Phase 1, Sprint 2 (Week 5–6): Pipeline + Kit Display

### DS1 — Kit Orchestrator
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Kit Orchestrator: pipeline controller (state machine) | Pipeline with clear states |
| 3-4 | Parallel executor: asyncio.gather for concurrent AI calls | 5 parallel LLM calls |
| 5 | Kit assembler: collect outputs → unified kit JSON | Kit schema defined + assembly |
| 6 | Kit storage: PostgreSQL schema, save/retrieve kits | CRUD operations for kits |
| 7-8 | SSE streaming: real-time progress updates to client | `/stream/{job_id}` endpoint |
| 9 | Retry logic: handle partial failures gracefully | Robust error handling |

### DS2 — AI Engine (Rubric, Flags, Flow)
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Rubric Generator: weighted criteria + calibration | `POST /generate-rubric` working |
| 3-4 | Red Flags Analyzer: concerns + probes | `POST /analyze-red-flags` working |
| 5 | Flow Guide Generator: minute-by-minute structure | `POST /generate-flow` working |
| 6-7 | Match Scorer: resume × JD analysis | `POST /match-score` working |
| 8-9 | End-to-end testing: full pipeline with real data | All endpoints producing quality output |
| 10 | Performance optimization: streaming, parallel prompts | Sub-25s total generation time |

### FE1 — Kit Display UI
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Kit layout: section cards (questions, test, rubric, flags, flow) | Kit structure rendered |
| 3-4 | Question cards: expandable, with model answers + follow-ups | Interactive question display |
| 5 | Practical test section: task, criteria, difficulty tabs | Test display with variants |
| 6 | Rubric section: criteria table with scores | Visual rubric |
| 7-8 | SSE client: real-time progress bar + section-by-section reveal | Streaming generation UX |
| 9 | Red flags + flow guide sections | All sections rendered |

---

## Phase 1, Sprint 3 (Week 7–8): Auth, Export, Launch

### DS1 — Auth + Export + Polish
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Auth Service: email registration + login (JWT) | Working auth flow |
| 3 | Auth Service: Google OAuth integration | Google sign-in working |
| 4 | Auth Service: usage tracking + free tier limits | 3 kits/month enforcement |
| 5-6 | Export Service: PDF generation (WeasyPrint + Jinja2 templates) | `POST /generate-pdf` → PDF file |
| 7 | Export Service: shareable links (UUID routes) | Public share URLs |
| 8 | Gateway: integrate auth verification on all routes | Auth enforced end-to-end |
| 9-10 | Integration testing + bug fixes + deployment | All services running in prod |

### DS2 — Quality Refinement + Testing
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-3 | Prompt refinement: test with 20+ varied resumes across roles | Prompt quality at production level |
| 4-5 | Edge cases: short resumes, vague JDs, unusual formats | Graceful handling of edge cases |
| 6-7 | Output quality audit: rate every generated kit section | Quality benchmark documented |
| 8 | Fallback logic: Claude → GPT-4 fallback on failures | LLM resilience |
| 9-10 | Full end-to-end integration testing with FE1 | Complete flow validated |

### FE1 — Auth UI + Dashboard + Export
| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Login/signup pages (email + Google OAuth) | Auth UI working |
| 3-4 | Dashboard: kit history, search, filter, delete | Kit management |
| 5 | PDF download button (trigger export, download file) | One-click PDF |
| 6 | Share kit flow (generate link, copy to clipboard) | Sharing working |
| 7-8 | Free tier UI (usage counter, upgrade prompt) | Tier limits visible |
| 9-10 | Polish: loading states, error states, mobile responsive | Production-ready UI |

---

## Coordination Points (Weekly)

| Day | Activity | Who |
|-----|----------|-----|
| Monday | Sprint planning + standup | ALL |
| Wednesday | Midweek sync (blockers, API contract reviews) | ALL |
| Friday | Demo + sprint review | ALL |

---

## API Contract Ownership

Each service owner defines and maintains their API contract:

| Contract | Owner | Consumers |
|----------|-------|-----------|
| Gateway routes + auth headers | DS1 | FE1 |
| Resume Service `/parse` schema | DS1 | Kit Orchestrator (DS1) |
| AI Engine all endpoints schema | DS2 | Kit Orchestrator (DS1) |
| Kit Orchestrator `/generate` + SSE | DS1 | Frontend (FE1) |
| Export Service `/generate-pdf` | DS1 | Frontend (FE1) |
| Auth Service `/login`, `/register` | DS1 | Frontend (FE1) |

**Rule:** API contracts are defined in `shared/schemas/` as Pydantic models. Any breaking change requires a notification to all consumers.

---

## Shared Responsibilities

| Task | Who | When |
|------|-----|------|
| Code review | Rotate (any 2 of 3) | Every PR |
| Database migrations | DS1 | As needed |
| Deployment | DS1 (infra lead) | Every Friday |
| Prompt versioning | DS2 | Continuous |
| API documentation | Owner of each service | With each endpoint |
| Integration testing | ALL | Sprint 3 + before each release |

---

## Phase 2+ Task Preview

### DS1 (Week 9-16)
- Candidate comparison backend logic
- Post-interview debrief storage + API
- Team workspace (multi-tenant RLS)
- Stripe billing integration
- ATS integration (Greenhouse/Lever)

### DS2 (Week 9-16)
- Comparison scoring algorithms
- Feedback loop pipeline
- Role template library (15-20 roles)
- Prompt quality analysis + A/B testing
- Interviewer calibration analytics

### FE1 (Week 9-16)
- Candidate comparison dashboard (radar charts)
- Debrief form UI
- Team workspace UI
- Billing/subscription pages
- SEO interview question pages (programmatic)

---

## Definition of Done (per task)

- [ ] Code written and passing lint
- [ ] Unit tests cover happy path + main edge cases
- [ ] API endpoint documented (OpenAPI spec auto-generated)
- [ ] PR reviewed by at least 1 other team member
- [ ] Works in Docker Compose locally
- [ ] No security vulnerabilities (no secrets in code, input validation)

---

## Communication Tools

| Purpose | Tool |
|---------|------|
| Daily async updates | Slack / Discord |
| Sprint planning | Notion / Linear |
| API contracts | OpenAPI specs in repo |
| Design mockups | Figma |
| Code | GitHub (branch per feature, squash merge) |
| CI/CD | GitHub Actions |
| Deployment | Railway dashboard |
