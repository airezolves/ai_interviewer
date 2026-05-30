-- InterviewKit AI — Database Initialization
-- This runs on first docker-compose up

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
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

-- Parsed resumes cache (must be created BEFORE kits table)
CREATE TABLE IF NOT EXISTS parsed_resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(500),
    raw_text TEXT,
    structured_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Kits table
CREATE TABLE IF NOT EXISTS kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parsed_resume_id UUID REFERENCES parsed_resumes(id) ON DELETE SET NULL,
    title VARCHAR(255),
    role_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    jd_text TEXT NOT NULL,
    resume_text TEXT,
    resume_file_url VARCHAR(500),
    structured_resume JSONB,
    structured_jd JSONB,
    match_analysis JSONB,
    questions JSONB,
    practical_test JSONB,
    rubric JSONB,
    red_flags JSONB,
    flow_guide JSONB,
    pdf_url VARCHAR(500),
    share_token UUID UNIQUE DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generation jobs (tracks pipeline progress)
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

-- Feedback (Phase 2)
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_kits_user_id ON kits(user_id);
CREATE INDEX IF NOT EXISTS idx_kits_status ON kits(status);
CREATE INDEX IF NOT EXISTS idx_kits_created_at ON kits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_kits_share_token ON kits(share_token);
CREATE INDEX IF NOT EXISTS idx_kits_parsed_resume_id ON kits(parsed_resume_id);
CREATE INDEX IF NOT EXISTS idx_jobs_kit_id ON generation_jobs(kit_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_parsed_resumes_hash ON parsed_resumes(file_hash);
CREATE INDEX IF NOT EXISTS idx_parsed_resumes_user_id ON parsed_resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
