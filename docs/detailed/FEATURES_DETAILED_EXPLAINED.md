# Feature-by-Feature Detailed Explanation (ai_interviewer)

This document explains each core feature in detail: what it does, how it works, the code flow, main modules, tech stack, and tools used.

---

## 1. User Authentication (Email/Google, JWT, Free Tier)
- **Functionality:**
  - Register/login with email+password or Google OAuth
  - JWT access/refresh tokens for session
  - Free tier: 3 kits/month/user
- **Code Flow:**
  - Frontend `/login` page calls `/api/v1/auth/register` or `/login` (gateway → auth service)
  - Auth service verifies credentials, hashes passwords (bcrypt), issues JWTs
  - JWT verified by gateway middleware for protected routes
  - Usage tracked in users table, enforced by `/can-generate` endpoint
- **Main Modules:**
  - backend/auth/app/routes/auth.py, users.py
  - backend/auth/app/services/password.py
  - shared/auth/__init__.py, shared/schemas/auth.py
  - backend/gateway/app/middleware/auth.py
  - frontend/src/app/login/, frontend/src/lib/api-client.ts
- **Tech Stack:** FastAPI, pyjwt, passlib[bcrypt], httpx, PostgreSQL, Next.js, Zustand

---

## 2. Resume Parsing (PDF/DOCX, LLM Structuring, Caching)
- **Functionality:**
  - Upload PDF/DOCX or paste text
  - Extract text, structure with LLM, cache by file hash
- **Code Flow:**
  - Frontend `/generate` page uploads file to `/api/v1/resume/parse`
  - Resume service extracts text (PyMuPDF/python-docx), hashes file, checks cache
  - Calls LLM (Claude) for structuring, stores result in DB
  - Returns `StructuredResume` JSON
- **Main Modules:**
  - backend/resume/app/routes/parse.py
  - backend/resume/app/parser/pdf_parser.py, docx_parser.py, llm_structurer.py
  - shared/schemas/resume.py, shared/database/models.py
  - frontend/src/components/file-upload.tsx, frontend/src/app/generate/
- **Tech Stack:** FastAPI, PyMuPDF, python-docx, anthropic, SQLAlchemy, Next.js

---

## 3. Job Description (JD) Analysis
- **Functionality:**
  - Parse unstructured JD text into structured fields (skills, responsibilities, seniority)
- **Code Flow:**
  - `/api/v1/ai_engine/analyze-jd` endpoint (gateway → ai_engine)
  - ai_engine/generators/jd_analyzer.py calls LLM, parses output
- **Main Modules:**
  - backend/ai_engine/app/routes/analyze.py
  - backend/ai_engine/app/generators/jd_analyzer.py
  - shared/schemas/kit.py
- **Tech Stack:** FastAPI, anthropic/openai, Pydantic

---

## 4. Resume-JD Match Scoring
- **Functionality:**
  - Compute compatibility score, skill matches/gaps
- **Code Flow:**
  - `/api/v1/ai_engine/match-score` endpoint
  - ai_engine/generators/match_scorer.py calls LLM, returns `MatchAnalysis`
- **Main Modules:**
  - backend/ai_engine/app/routes/analyze.py
  - backend/ai_engine/app/generators/match_scorer.py
  - shared/schemas/kit.py
- **Tech Stack:** FastAPI, anthropic/openai

---

## 5. Question Generation
- **Functionality:**
  - Generate 10 tailored questions (behavioral, technical, system design) with model answers
- **Code Flow:**
  - `/api/v1/ai_engine/generate-questions` endpoint
  - ai_engine/generators/question_generator.py builds prompt, calls LLM, parses JSON
  - Fallback to generic questions if LLM fails
- **Main Modules:**
  - backend/ai_engine/app/routes/generate.py
  - backend/ai_engine/app/generators/question_generator.py, llm_client.py
  - shared/schemas/kit.py
  - frontend/src/components/kit-viewer.tsx
- **Tech Stack:** FastAPI, anthropic/openai, Pydantic, Next.js

---

## 6. Practical Test Generation
- **Functionality:**
  - Generate practical assessment with 3 difficulty variants
- **Code Flow:**
  - `/api/v1/ai_engine/generate-test` endpoint
  - ai_engine/generators/test_generator.py builds prompt, calls LLM, parses JSON
- **Main Modules:**
  - backend/ai_engine/app/routes/generate.py
  - backend/ai_engine/app/generators/test_generator.py, llm_client.py
  - shared/schemas/kit.py
  - frontend/src/components/kit-viewer.tsx
- **Tech Stack:** FastAPI, anthropic/openai, Pydantic, Next.js

---

## 7. Scoring Rubric Generation
- **Functionality:**
  - Generate 8 weighted criteria with calibration examples
- **Code Flow:**
  - `/api/v1/ai_engine/generate-rubric` endpoint
  - ai_engine/generators/rubric_generator.py builds prompt, calls LLM, parses JSON
- **Main Modules:**
  - backend/ai_engine/app/routes/generate.py
  - backend/ai_engine/app/generators/rubric_generator.py, llm_client.py
  - shared/schemas/kit.py
  - frontend/src/components/kit-viewer.tsx
- **Tech Stack:** FastAPI, anthropic/openai, Pydantic, Next.js

---

## 8. Red Flags Analysis
- **Functionality:**
  - Identify 3-5 concerns, generate probe questions
- **Code Flow:**
  - `/api/v1/ai_engine/generate-red-flags` endpoint
  - ai_engine/generators/red_flags_generator.py builds prompt, calls LLM, parses JSON
- **Main Modules:**
  - backend/ai_engine/app/routes/generate.py
  - backend/ai_engine/app/generators/red_flags_generator.py, llm_client.py
  - shared/schemas/kit.py
  - frontend/src/components/kit-viewer.tsx
- **Tech Stack:** FastAPI, anthropic/openai, Pydantic, Next.js

---

## 9. Interview Flow Guide Generation
- **Functionality:**
  - Generate 60-min interview structure, map questions to sections
- **Code Flow:**
  - `/api/v1/ai_engine/generate-flow` endpoint
  - ai_engine/generators/flow_generator.py builds prompt, calls LLM, parses JSON
- **Main Modules:**
  - backend/ai_engine/app/routes/generate.py
  - backend/ai_engine/app/generators/flow_generator.py, llm_client.py
  - shared/schemas/kit.py
  - frontend/src/components/kit-viewer.tsx
- **Tech Stack:** FastAPI, anthropic/openai, Pydantic, Next.js

---

## 10. Pipeline Orchestration & Job Tracking
- **Functionality:**
  - Orchestrate all steps, track job status, SSE progress
- **Code Flow:**
  - `/api/v1/kits/generate` endpoint (gateway → kit_orchestrator)
  - kit_orchestrator/pipeline/controller.py runs pipeline (asyncio.gather)
  - Updates GenerationJob and Kit models, streams progress
- **Main Modules:**
  - backend/kit_orchestrator/app/routes/generate.py, kits.py
  - backend/kit_orchestrator/app/pipeline/controller.py
  - shared/database/models.py, shared/schemas/kit.py
  - frontend/src/app/generate/, dashboard/, kit/
- **Tech Stack:** FastAPI, httpx, asyncio, SQLAlchemy, SSE, Next.js

---

## 11. PDF Export
- **Functionality:**
  - Render kit as branded PDF, download link
- **Code Flow:**
  - `/api/v1/export/pdf/{kit_id}` endpoint
  - export/services/pdf_renderer.py loads kit, renders Jinja2 template, WeasyPrint to PDF
- **Main Modules:**
  - backend/export/app/routes/pdf.py
  - backend/export/app/services/pdf_renderer.py
  - backend/export/app/templates/kit_pdf.html
  - shared/database/models.py
  - frontend/src/components/kit-viewer.tsx
- **Tech Stack:** FastAPI, Jinja2, WeasyPrint, SQLAlchemy, Next.js

---

## 12. Shareable Kit Links
- **Functionality:**
  - Generate public URL for kit, view without login
- **Code Flow:**
  - `/api/v1/export/share/{kit_id}` endpoint
  - export/routes/share.py generates UUID token, stores in kit, returns URL
  - `/api/v1/kits/shared/{token}` endpoint (kit_orchestrator)
- **Main Modules:**
  - backend/export/app/routes/share.py
  - backend/kit_orchestrator/app/routes/kits.py
  - shared/database/models.py
  - frontend/src/app/kit/
- **Tech Stack:** FastAPI, SQLAlchemy, Next.js

---

## 13. Rate Limiting
- **Functionality:**
  - Enforce per-user/IP request limits (10/min free, 60/min pro)
- **Code Flow:**
  - gateway/app/middleware/rate_limiter.py checks Redis, increments counter, blocks if over limit
- **Main Modules:**
  - backend/gateway/app/middleware/rate_limiter.py
  - backend/gateway/app/config.py
- **Tech Stack:** FastAPI, Redis, Starlette

---

## 14. LLM Fallback (Claude → GPT-4)
- **Functionality:**
  - Use Claude by default, fallback to GPT-4 if error/rate limit
- **Code Flow:**
  - ai_engine/generators/llm_client.py tries Anthropic, falls back to OpenAI
- **Main Modules:**
  - backend/ai_engine/app/generators/llm_client.py
  - backend/ai_engine/app/config.py
- **Tech Stack:** anthropic, openai

---

## 15. Database Models & Schemas
- **Functionality:**
  - Define all DB tables and API schemas
- **Main Modules:**
  - shared/database/models.py
  - shared/schemas/
- **Tech Stack:** SQLAlchemy, Pydantic

---

## 16. Frontend Integration
- **Functionality:**
  - UI for all flows, file upload, kit display, SSE progress, login, dashboard
- **Main Modules:**
  - frontend/src/app/
  - frontend/src/components/
  - frontend/src/lib/api-client.ts
  - frontend/src/types/index.ts
- **Tech Stack:** Next.js, TypeScript, Tailwind CSS, Zustand, Axios

---

*For code references, see the Feature-to-Module Map. For architecture, see FULL_SYSTEM_DOCUMENTATION.md.*
