-- =============================================================================
-- PlayWithPDFs Database Schema (PostgreSQL)
-- Compatible with PostgreSQL 12+, TimescaleDB, Neon, Supabase, Render, Railway
-- =============================================================================

-- 1. Table: admin_users
-- Stores administrator and viewer accounts for the admin panel.
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(190) NOT NULL UNIQUE,
    name VARCHAR(120),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',        -- 'admin' | 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_admin_users_email ON admin_users (email);


-- 2. Table: users
-- Stores registered end-users of the PlayWithPDFs web application.
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(190) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);


-- 2. Table: tool_configs
-- Controls runtime configuration and kill-switches for each PDF tool.
CREATE TABLE IF NOT EXISTS tool_configs (
    id SERIAL PRIMARY KEY,
    tool VARCHAR(60) NOT NULL UNIQUE,
    label VARCHAR(120),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    maintenance_note VARCHAR(255),
    max_file_mb INTEGER DEFAULT 50,
    max_files INTEGER DEFAULT 20,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_tool_configs_tool ON tool_configs (tool);


-- 3. Table: tool_events
-- Analytics and error tracking table (records every tool invocation).
CREATE TABLE IF NOT EXISTS tool_events (
    id BIGSERIAL PRIMARY KEY,
    tool VARCHAR(60) NOT NULL,
    endpoint VARCHAR(120),
    method VARCHAR(8),
    status_code INTEGER,
    ok BOOLEAN DEFAULT TRUE,
    duration_ms INTEGER,
    input_bytes BIGINT DEFAULT 0,
    output_bytes BIGINT DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    visitor VARCHAR(64),                     -- SHA-256 hashed IP
    user_agent VARCHAR(255),
    error_text TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_tool_events_tool ON tool_events (tool);
CREATE INDEX IF NOT EXISTS ix_tool_events_status_code ON tool_events (status_code);
CREATE INDEX IF NOT EXISTS ix_tool_events_ok ON tool_events (ok);
CREATE INDEX IF NOT EXISTS ix_tool_events_visitor ON tool_events (visitor);
CREATE INDEX IF NOT EXISTS ix_tool_events_created_at ON tool_events (created_at);


-- 4. Table: contact_messages
-- Stores messages submitted through the Contact Us page.
CREATE TABLE IF NOT EXISTS contact_messages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120),
    email VARCHAR(190),
    subject VARCHAR(200),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'new',        -- 'new' | 'open' | 'closed'
    email_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    handled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_contact_messages_email ON contact_messages (email);
CREATE INDEX IF NOT EXISTS ix_contact_messages_status ON contact_messages (status);
CREATE INDEX IF NOT EXISTS ix_contact_messages_created_at ON contact_messages (created_at);


-- 5. Table: audit_logs
-- Tracks changes made in the admin panel by administrators.
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    admin_email VARCHAR(190),
    action VARCHAR(80) NOT NULL,
    target VARCHAR(120),
    detail TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);


-- =============================================================================
-- SEED DATA: Pre-populate Tool Configurations
-- =============================================================================

INSERT INTO tool_configs (tool, label, enabled, max_file_mb, max_files) VALUES
    ('add_page_number', 'Add Page Number', TRUE, 50, 20),
    ('add_watermark', 'Add Watermark', TRUE, 50, 20),
    ('compare_pdf', 'Compare Pdf', TRUE, 50, 20),
    ('compress', 'Compress', TRUE, 50, 2),
    ('contact_us', 'Contact Us', TRUE, 50, 20),
    ('crop_pdf', 'Crop Pdf', TRUE, 50, 20),
    ('download', 'Download', TRUE, 50, 20),
    ('edit_pdf', 'Edit Pdf', TRUE, 50, 20),
    ('excel_to_pdf', 'Excel To Pdf', TRUE, 50, 20),
    ('extract_pages', 'Extract Pages', TRUE, 50, 20),
    ('html_to_pdf', 'Html To Pdf', TRUE, 50, 20),
    ('jpg_to_pdf', 'Jpg To Pdf', TRUE, 50, 20),
    ('merge', 'Merge', TRUE, 50, 20),
    ('ocr_to_pdf', 'Ocr To Pdf', TRUE, 50, 20),
    ('organize_pdf', 'Organize Pdf', TRUE, 50, 20),
    ('pdf_to_excel', 'Pdf To Excel', TRUE, 50, 20),
    ('pdf_to_jpg', 'Pdf To Jpg', TRUE, 50, 20),
    ('pdf_to_pdfA', 'Pdf To Pdfa', TRUE, 50, 20),
    ('pdf_to_ppt', 'Pdf To Ppt', TRUE, 50, 20),
    ('pdf_to_word', 'Pdf To Word', TRUE, 50, 20),
    ('ppt_to_pdf', 'Ppt To Pdf', TRUE, 50, 20),
    ('protect_pdf', 'Protect Pdf', TRUE, 50, 20),
    ('redact_pdf', 'Redact Pdf', TRUE, 50, 20),
    ('remove_pages', 'Remove Pages', TRUE, 50, 20),
    ('repair', 'Repair', TRUE, 50, 20),
    ('rotate_pdf', 'Rotate Pdf', TRUE, 50, 20),
    ('sign_pdf', 'Sign Pdf', TRUE, 50, 20),
    ('split', 'Split', TRUE, 50, 20),
    ('translate', 'Translate', TRUE, 50, 20),
    ('unlock_pdf', 'Unlock Pdf', TRUE, 50, 20),
    ('word_to_pdf', 'Word To Pdf', TRUE, 50, 20)
ON CONFLICT (tool) DO NOTHING;


-- =============================================================================
-- SEED DATA: Default Admin User
-- Email: smitghori83@gmail.com
-- =============================================================================

INSERT INTO admin_users (email, name, password_hash, role, is_active) VALUES
    ('smitghori83@gmail.com', 'Admin', 'scrypt:32768:8:1$ZkRsJP8Leo6axzya$616272bd344d654efb32f2a9135d1270ca6661cef4b849adaa53c2aee58b1da7c112683d0e15995e09f2f187a882b05a3eca350ff15aec492aae084dfab3987d', 'admin', TRUE)
ON CONFLICT (email) DO NOTHING;
