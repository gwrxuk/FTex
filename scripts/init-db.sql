-- FTex Database Initialization Script
-- Creates tables, indexes, and seed data for the Decision Intelligence Platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM ('individual', 'organization', 'account', 'address', 'device', 'phone', 'email');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE transaction_type AS ENUM ('wire_transfer', 'ach', 'card_payment', 'cash_deposit', 'cash_withdrawal', 'internal_transfer', 'crypto', 'trade', 'fee', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('new', 'investigating', 'escalated', 'resolved_sar', 'resolved_false_positive', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE case_status AS ENUM ('open', 'in_progress', 'pending_review', 'escalated', 'sar_filed', 'closed_no_action', 'closed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- RFP/RFI related enums
DO $$ BEGIN
    CREATE TYPE proposal_type AS ENUM ('rfp', 'rfi', 'rfq', 'eoi');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE proposal_status AS ENUM ('draft', 'in_progress', 'review', 'submitted', 'won', 'lost', 'no_bid', 'withdrawn');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE proposal_priority AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- RFP/RFI Proposals Table
CREATE TABLE IF NOT EXISTS proposals (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    proposal_number VARCHAR(50) UNIQUE NOT NULL,
    proposal_type proposal_type NOT NULL,
    
    -- Client Information
    client_name VARCHAR(255) NOT NULL,
    client_industry VARCHAR(100),
    client_country VARCHAR(100),
    client_contact_name VARCHAR(255),
    client_contact_email VARCHAR(255),
    client_contact_phone VARCHAR(50),
    
    -- Proposal Details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    requirements_summary TEXT,
    
    -- Status
    status proposal_status DEFAULT 'draft',
    priority proposal_priority DEFAULT 'medium',
    
    -- Solution Areas
    solution_areas JSONB DEFAULT '[]'::jsonb,
    use_cases JSONB DEFAULT '[]'::jsonb,
    
    -- Timeline
    received_date TIMESTAMP,
    due_date TIMESTAMP,
    submitted_date TIMESTAMP,
    decision_date TIMESTAMP,
    
    -- Financials
    estimated_deal_value DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Team
    lead_owner VARCHAR(100),
    team_members JSONB DEFAULT '[]'::jsonb,
    reviewers JSONB DEFAULT '[]'::jsonb,
    
    -- Content
    response_sections JSONB DEFAULT '[]'::jsonb,
    technical_requirements JSONB DEFAULT '[]'::jsonb,
    compliance_requirements JSONB DEFAULT '[]'::jsonb,
    
    -- Attachments
    attachments JSONB DEFAULT '[]'::jsonb,
    
    -- Evaluation
    win_probability DECIMAL(3, 2) DEFAULT 0.50,
    competition JSONB DEFAULT '[]'::jsonb,
    differentiators JSONB DEFAULT '[]'::jsonb,
    risks JSONB DEFAULT '[]'::jsonb,
    
    -- Outcome
    outcome_reason TEXT,
    lessons_learned TEXT,
    
    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Proposal Sections Table
CREATE TABLE IF NOT EXISTS proposal_sections (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    proposal_id VARCHAR(36) REFERENCES proposals(id) ON DELETE CASCADE,
    
    section_number VARCHAR(50),
    title VARCHAR(500),
    question TEXT,
    
    response TEXT,
    response_status VARCHAR(50) DEFAULT 'pending',
    
    assigned_to VARCHAR(100),
    reviewer VARCHAR(100),
    
    category VARCHAR(100),
    is_mandatory INTEGER DEFAULT 1,
    
    max_score INTEGER,
    weight DECIMAL(5, 2) DEFAULT 1.0,
    
    attachments JSONB DEFAULT '[]'::jsonb,
    content_library_refs JSONB DEFAULT '[]'::jsonb,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content Library Table
CREATE TABLE IF NOT EXISTS content_library (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    
    category VARCHAR(100),
    subcategory VARCHAR(100),
    solution_area VARCHAR(100),
    
    tags JSONB DEFAULT '[]'::jsonb,
    keywords JSONB DEFAULT '[]'::jsonb,
    
    version VARCHAR(20) DEFAULT '1.0',
    is_current INTEGER DEFAULT 1,
    
    usage_count INTEGER DEFAULT 0,
    last_used_date TIMESTAMP,
    
    last_reviewed_date TIMESTAMP,
    reviewed_by VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Insert sample entities for demonstration
INSERT INTO entities (id, entity_type, name, risk_score, is_sanctioned, is_pep, attributes, source_systems, created_at)
VALUES
    (uuid_generate_v4(), 'organization', 'Acme Trading Corp', 0.35, 0, 0, '{"industry": "trading", "country": "SG"}', '["core_banking", "crm"]', NOW()),
    (uuid_generate_v4(), 'individual', 'John Smith', 0.72, 0, 1, '{"nationality": "US", "occupation": "executive"}', '["kyc_system"]', NOW()),
    (uuid_generate_v4(), 'organization', 'Global Investments Ltd', 0.85, 1, 0, '{"industry": "finance", "country": "KY"}', '["trade_system"]', NOW()),
    (uuid_generate_v4(), 'account', 'ACC-001-2024-SG', 0.45, 0, 0, '{"type": "checking", "currency": "SGD"}', '["core_banking"]', NOW()),
    (uuid_generate_v4(), 'individual', 'Sarah Chen', 0.22, 0, 0, '{"nationality": "SG", "occupation": "manager"}', '["kyc_system"]', NOW())
ON CONFLICT DO NOTHING;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_risk ON entities(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_entities_sanctioned ON entities(is_sanctioned) WHERE is_sanctioned = 1;
CREATE INDEX IF NOT EXISTS idx_entities_pep ON entities(is_pep) WHERE is_pep = 1;
CREATE INDEX IF NOT EXISTS idx_entities_name_trgm ON entities USING gin(name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_sender ON transactions(sender_entity_id);
CREATE INDEX IF NOT EXISTS idx_transactions_receiver ON transactions(receiver_entity_id);
CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_flagged ON transactions(is_flagged) WHERE is_flagged = 1;

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_detected ON alerts(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_assigned ON alerts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_alerts_entity ON alerts(primary_entity_id);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_priority ON cases(priority);
CREATE INDEX IF NOT EXISTS idx_cases_assigned ON cases(assigned_to);

-- RFP/RFI indexes
CREATE INDEX IF NOT EXISTS idx_proposals_type ON proposals(proposal_type);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_priority ON proposals(priority);
CREATE INDEX IF NOT EXISTS idx_proposals_client ON proposals(client_name);
CREATE INDEX IF NOT EXISTS idx_proposals_due ON proposals(due_date);
CREATE INDEX IF NOT EXISTS idx_proposals_lead ON proposals(lead_owner);
CREATE INDEX IF NOT EXISTS idx_proposal_sections_proposal ON proposal_sections(proposal_id);
CREATE INDEX IF NOT EXISTS idx_content_library_category ON content_library(category);
CREATE INDEX IF NOT EXISTS idx_content_library_solution ON content_library(solution_area);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DO $$ BEGIN
    CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_proposal_sections_updated_at BEFORE UPDATE ON proposal_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_content_library_updated_at BEFORE UPDATE ON content_library
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Insert sample RFP data for demonstration
INSERT INTO proposals (id, proposal_number, proposal_type, client_name, client_industry, client_country, title, description, status, priority, solution_areas, due_date, estimated_deal_value, lead_owner, win_probability, created_at)
VALUES
    (uuid_generate_v4()::text, 'RFP-202501-0001', 'rfp', 'DBS Bank', 'Banking', 'Singapore', 'AML Transaction Monitoring Solution', 'End-to-end AML transaction monitoring with entity resolution capabilities', 'in_progress', 'high', '["AML", "Transaction Monitoring", "Entity Resolution"]', NOW() + INTERVAL '30 days', 2500000.00, 'solution_engineer_1', 0.65, NOW()),
    (uuid_generate_v4()::text, 'RFP-202501-0002', 'rfp', 'UOB', 'Banking', 'Singapore', 'Fraud Detection Platform', 'Real-time fraud detection with network analytics', 'review', 'critical', '["Fraud Detection", "Network Analytics", "Real-time Monitoring"]', NOW() + INTERVAL '14 days', 1800000.00, 'solution_engineer_2', 0.72, NOW()),
    (uuid_generate_v4()::text, 'RFI-202501-0001', 'rfi', 'OCBC', 'Banking', 'Singapore', 'KYC/CDD Enhancement Solution', 'Information request for KYC customer due diligence platform', 'draft', 'medium', '["KYC", "CDD", "Entity Resolution"]', NOW() + INTERVAL '45 days', 1200000.00, 'solution_engineer_1', 0.50, NOW()),
    (uuid_generate_v4()::text, 'RFP-202412-0001', 'rfp', 'Standard Chartered', 'Banking', 'Singapore', 'Enterprise Sanctions Screening', 'Global sanctions screening with PEP and adverse media', 'won', 'high', '["Sanctions Screening", "PEP", "Risk Management"]', NOW() - INTERVAL '30 days', 3200000.00, 'solution_engineer_1', 1.00, NOW() - INTERVAL '60 days'),
    (uuid_generate_v4()::text, 'RFP-202411-0001', 'rfp', 'MUFG', 'Banking', 'Singapore', 'Trade Finance Compliance', 'Trade finance transaction monitoring and compliance', 'lost', 'high', '["Trade Finance", "Compliance", "Transaction Monitoring"]', NOW() - INTERVAL '45 days', 1500000.00, 'solution_engineer_2', 0.00, NOW() - INTERVAL '90 days')
ON CONFLICT DO NOTHING;

-- Insert sample content library items
INSERT INTO content_library (id, title, content, category, solution_area, tags, usage_count, created_at)
VALUES
    (uuid_generate_v4()::text, 'Entity Resolution Overview', 'Our entity resolution engine uses advanced fuzzy matching algorithms combined with machine learning to accurately identify and link records representing the same real-world entity across disparate data sources. Key capabilities include: name matching with cultural awareness, address standardization and matching, document ID verification, and probabilistic record linkage.', 'technical', 'Entity Resolution', '["entity resolution", "data quality", "fuzzy matching"]', 15, NOW()),
    (uuid_generate_v4()::text, 'Network Analytics Description', 'The network analytics module provides graph-based analysis of entity relationships to identify complex financial crime patterns. Features include: automated network generation, community detection, centrality analysis, path analysis for money flow, and risk propagation through connected entities.', 'technical', 'Network Analytics', '["network analysis", "graph", "relationships"]', 12, NOW()),
    (uuid_generate_v4()::text, 'AML Compliance Statement', 'Our solution fully supports compliance with regulatory requirements including MAS Notice 626, FATF recommendations, and global AML/CFT standards. We provide configurable rules, full audit trails, SAR generation capabilities, and regulatory reporting.', 'compliance', 'AML', '["compliance", "regulatory", "MAS", "FATF"]', 23, NOW()),
    (uuid_generate_v4()::text, 'Implementation Methodology', 'We follow an agile implementation methodology with typical project phases: Discovery (4-6 weeks), Configuration (6-8 weeks), Integration (4-6 weeks), UAT (4 weeks), and Go-Live support (4 weeks). Total implementation typically ranges from 4-6 months depending on scope.', 'project', 'Implementation', '["implementation", "methodology", "timeline"]', 18, NOW()),
    (uuid_generate_v4()::text, 'Security and Data Protection', 'The platform implements enterprise-grade security including: encryption at rest (AES-256) and in transit (TLS 1.3), role-based access control, SSO/SAML integration, comprehensive audit logging, and data residency compliance. We maintain SOC 2 Type II certification.', 'security', 'Security', '["security", "encryption", "SOC2"]', 28, NOW())
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ftex;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ftex;

COMMENT ON DATABASE ftex_db IS 'FTex Decision Intelligence Platform - Financial Crime Detection Database';

