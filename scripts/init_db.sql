-- InterviewKit AI — Database Initialization (v2 agentic)
-- This runs on first docker-compose up (or against an empty DB).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Users ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    auth_provider VARCHAR(50) DEFAULT 'email',
    plan VARCHAR(20) DEFAULT 'free',
    kits_generated_this_month INT DEFAULT 0,
    monthly_reset_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Kits ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    role_type VARCHAR(50) NOT NULL,
    -- pending → matching → match_ready → (denied | interviewing) → analyzed → complete | failed
    status VARCHAR(20) DEFAULT 'pending',
    jd_text TEXT NOT NULL,
    resume_text TEXT,
    resume_file_url VARCHAR(500),
    structured_resume JSONB,
    structured_jd JSONB,
    match_analysis JSONB,
    proceed_decision VARCHAR(20),
    proceed_decided_at TIMESTAMPTZ,
    pdf_url VARCHAR(500),
    share_token UUID UNIQUE DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Generation jobs (used during the matching phase) ──────────────
CREATE TABLE IF NOT EXISTS generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID REFERENCES kits(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    current_step VARCHAR(50),
    progress_pct INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Parsed resumes cache ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parsed_resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    raw_text TEXT,
    structured_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Per-user LLM providers (encrypted keys) ───────────────────────
CREATE TABLE IF NOT EXISTS user_llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(150) NOT NULL,
    display_name VARCHAR(200),
    endpoint VARCHAR(500),
    api_key_encrypted TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Interview sessions ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    plan JSONB,
    current_turn_index INT NOT NULL DEFAULT 0,
    max_turns INT NOT NULL DEFAULT 10,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ── Q&A turns ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS qa_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    turn_index INT NOT NULL,
    question TEXT NOT NULL,
    question_type VARCHAR(30),
    topic VARCHAR(150),
    agent_thoughts TEXT,
    answer TEXT,
    asked_at TIMESTAMPTZ DEFAULT NOW(),
    answered_at TIMESTAMPTZ,
    UNIQUE (session_id, turn_index)
);

-- ── Final analyses ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS final_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    overall_score NUMERIC(5,2),
    dimension_scores JSONB,
    pros JSONB,
    cons JSONB,
    recommendation VARCHAR(20),
    role_suitability TEXT,
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Feedback (Phase 2) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kit_id UUID REFERENCES kits(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    questions_rating INT CHECK (questions_rating BETWEEN 1 AND 5),
    test_appropriate BOOLEAN,
    overall_rating INT CHECK (overall_rating BETWEEN 1 AND 5),
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_kits_user_id ON kits(user_id);
CREATE INDEX IF NOT EXISTS idx_kits_status ON kits(status);
CREATE INDEX IF NOT EXISTS idx_kits_created_at ON kits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_kits_share_token ON kits(share_token);
CREATE INDEX IF NOT EXISTS idx_jobs_kit_id ON generation_jobs(kit_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_parsed_resumes_hash ON parsed_resumes(file_hash);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_llm_providers_user_id ON user_llm_providers(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_llm_providers_active
    ON user_llm_providers(user_id) WHERE is_active = TRUE;
CREATE UNIQUE INDEX IF NOT EXISTS uq_interview_sessions_kit_id ON interview_sessions(kit_id);
CREATE INDEX IF NOT EXISTS idx_qa_turns_session_id ON qa_turns(session_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_final_analyses_kit_id ON final_analyses(kit_id);
