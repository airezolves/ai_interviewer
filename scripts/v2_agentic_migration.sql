-- ═══════════════════════════════════════════════════════════════
--  v2 Agentic Migration
--  Drops the old "generate-everything-up-front" columns and adds
--  the new agentic tables: user_llm_providers, interview_sessions,
--  qa_turns, final_analyses.
--
--  Idempotent — safe to run multiple times.
-- ═══════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. Drop obsolete kit columns (old generators replaced by agents) ──
ALTER TABLE kits DROP COLUMN IF EXISTS questions;
ALTER TABLE kits DROP COLUMN IF EXISTS practical_test;
ALTER TABLE kits DROP COLUMN IF EXISTS rubric;
ALTER TABLE kits DROP COLUMN IF EXISTS red_flags;
ALTER TABLE kits DROP COLUMN IF EXISTS flow_guide;

-- Add a "proceed gate" decision column so we know whether the recruiter
-- approved the candidate after seeing the match score.
ALTER TABLE kits ADD COLUMN IF NOT EXISTS proceed_decision VARCHAR(20);
-- Values: NULL (not decided), 'proceed', 'denied'
ALTER TABLE kits ADD COLUMN IF NOT EXISTS proceed_decided_at TIMESTAMPTZ;

-- Status now uses a richer state machine:
--   pending → matching → match_ready → (denied | interviewing) → analyzed → complete | failed

-- ── 2. Per-user LLM providers (encrypted API keys) ───────────────────
CREATE TABLE IF NOT EXISTS user_llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,         -- gemini | openai | anthropic | deepseek | azure | openai-compatible
    model VARCHAR(150) NOT NULL,
    display_name VARCHAR(200),
    endpoint VARCHAR(500),                 -- only for openai-compatible / internal
    api_key_encrypted TEXT,                -- AES-256-GCM ciphertext (base64)
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_llm_providers_user_id ON user_llm_providers(user_id);
-- Only one active provider per user (partial unique index)
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_llm_providers_active
    ON user_llm_providers(user_id) WHERE is_active = TRUE;

-- ── 3. Interview sessions (one per kit, drives the runtime agent) ───
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',  -- in_progress | completed | abandoned
    plan JSONB,                            -- list of planned topics/seed questions from the agent's plan step
    current_turn_index INT NOT NULL DEFAULT 0,
    max_turns INT NOT NULL DEFAULT 10,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_interview_sessions_kit_id ON interview_sessions(kit_id);

-- ── 4. Q&A turns (one row per question/answer pair) ─────────────────
CREATE TABLE IF NOT EXISTS qa_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    turn_index INT NOT NULL,
    question TEXT NOT NULL,
    question_type VARCHAR(30),             -- planned | followup | clarification | wrap_up
    topic VARCHAR(150),
    agent_thoughts TEXT,                   -- the "think" output from the agent loop
    answer TEXT,
    asked_at TIMESTAMPTZ DEFAULT NOW(),
    answered_at TIMESTAMPTZ,
    UNIQUE (session_id, turn_index)
);
CREATE INDEX IF NOT EXISTS idx_qa_turns_session_id ON qa_turns(session_id);

-- ── 5. Final analyses (one per kit, produced by the analysis agent) ─
CREATE TABLE IF NOT EXISTS final_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    overall_score NUMERIC(5,2),
    dimension_scores JSONB,                -- {technical, communication, problem_solving, role_fit, ...}
    pros JSONB,                            -- list[str]
    cons JSONB,                            -- list[str]
    recommendation VARCHAR(20),            -- hire | no_hire | maybe
    role_suitability TEXT,
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_final_analyses_kit_id ON final_analyses(kit_id);
