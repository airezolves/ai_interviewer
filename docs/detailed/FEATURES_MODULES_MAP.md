# Feature-to-Module Mapping (ai_interviewer)

This document lists each core feature and the main modules/files in the repository that implement or support that feature. Use this as a reference to quickly locate the code for any feature.

---

| Feature | Main Modules/Files |
|---------|--------------------|
| **1. User Authentication (Email/Google, JWT, Free Tier)** | backend/auth/app/routes/auth.py, backend/auth/app/routes/users.py, backend/auth/app/services/password.py, shared/auth/__init__.py, shared/schemas/auth.py, shared/database/models.py, backend/gateway/app/middleware/auth.py, frontend/src/app/login/, frontend/src/lib/api-client.ts |
| **2. Resume Parsing (PDF/DOCX, LLM Structuring, Caching)** | backend/resume/app/routes/parse.py, backend/resume/app/parser/pdf_parser.py, backend/resume/app/parser/docx_parser.py, backend/resume/app/parser/llm_structurer.py, shared/schemas/resume.py, shared/database/models.py, frontend/src/components/file-upload.tsx, frontend/src/app/generate/ |
| **3. Job Description (JD) Analysis** | backend/ai_engine/app/routes/analyze.py, backend/ai_engine/app/generators/jd_analyzer.py, shared/schemas/kit.py |
| **4. Resume-JD Match Scoring** | backend/ai_engine/app/routes/analyze.py, backend/ai_engine/app/generators/match_scorer.py, shared/schemas/kit.py |
| **5. Question Generation** | backend/ai_engine/app/routes/generate.py, backend/ai_engine/app/generators/question_generator.py, backend/ai_engine/app/generators/llm_client.py, shared/schemas/kit.py, frontend/src/components/kit-viewer.tsx |
| **6. Practical Test Generation** | backend/ai_engine/app/routes/generate.py, backend/ai_engine/app/generators/test_generator.py, backend/ai_engine/app/generators/llm_client.py, shared/schemas/kit.py, frontend/src/components/kit-viewer.tsx |
| **7. Scoring Rubric Generation** | backend/ai_engine/app/routes/generate.py, backend/ai_engine/app/generators/rubric_generator.py, backend/ai_engine/app/generators/llm_client.py, shared/schemas/kit.py, frontend/src/components/kit-viewer.tsx |
| **8. Red Flags Analysis** | backend/ai_engine/app/routes/generate.py, backend/ai_engine/app/generators/red_flags_generator.py, backend/ai_engine/app/generators/llm_client.py, shared/schemas/kit.py, frontend/src/components/kit-viewer.tsx |
| **9. Interview Flow Guide Generation** | backend/ai_engine/app/routes/generate.py, backend/ai_engine/app/generators/flow_generator.py, backend/ai_engine/app/generators/llm_client.py, shared/schemas/kit.py, frontend/src/components/kit-viewer.tsx |
| **10. Pipeline Orchestration & Job Tracking** | backend/kit_orchestrator/app/routes/generate.py, backend/kit_orchestrator/app/routes/kits.py, backend/kit_orchestrator/app/pipeline/controller.py, shared/database/models.py, shared/schemas/kit.py, frontend/src/app/generate/, frontend/src/app/dashboard/, frontend/src/app/kit/ |
| **11. PDF Export** | backend/export/app/routes/pdf.py, backend/export/app/services/pdf_renderer.py, backend/export/app/templates/kit_pdf.html, shared/database/models.py, frontend/src/components/kit-viewer.tsx |
| **12. Shareable Kit Links** | backend/export/app/routes/share.py, backend/kit_orchestrator/app/routes/kits.py, shared/database/models.py, frontend/src/app/kit/ |
| **13. Rate Limiting** | backend/gateway/app/middleware/rate_limiter.py, backend/gateway/app/config.py |
| **14. LLM Fallback (Claude → GPT-4)** | backend/ai_engine/app/generators/llm_client.py, backend/ai_engine/app/config.py |
| **15. Database Models & Schemas** | shared/database/models.py, shared/schemas/ |
| **16. Frontend Integration** | frontend/src/app/, frontend/src/components/, frontend/src/lib/api-client.ts, frontend/src/types/index.ts |

---

*For more details, see the full documentation and code comments in each module.*
