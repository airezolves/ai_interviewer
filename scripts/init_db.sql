-- InterviewKit AI — Initial Database Schema
-- Run this to set up the database

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    kits_generated_this_month INTEGER NOT NULL DEFAULT 0,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Kits table
CREATE TABLE IF NOT EXISTS kits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    role_type VARCHAR(100) NOT NULL,
    jd_text TEXT NOT NULL,
    candidate_name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    share_token VARCHAR(64) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kits_user_id ON kits(user_id);
CREATE INDEX idx_kits_status ON kits(status);
CREATE INDEX idx_kits_share_token ON kits(share_token);

-- Kit sections table
CREATE TABLE IF NOT EXISTS kit_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kit_id UUID NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
    section_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kit_sections_kit_id ON kit_sections(kit_id);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kit_id UUID NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    questions_useful BOOLEAN,
    assessment_appropriate BOOLEAN,
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedback_kit_id ON feedback(kit_id);

-- Usage records (for billing tracking)
CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    kit_id UUID,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_user_id ON usage_records(user_id);
CREATE INDEX idx_usage_created_at ON usage_records(created_at);

-- Prompt templates (for versioned prompt management)
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_type VARCHAR(100) NOT NULL,
    section_type VARCHAR(50) NOT NULL,
    template_text TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompts_role_section ON prompt_templates(role_type, section_type);

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kits_updated_at BEFORE UPDATE ON kits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kit_sections_updated_at BEFORE UPDATE ON kit_sections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feedback_updated_at BEFORE UPDATE ON feedback FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
