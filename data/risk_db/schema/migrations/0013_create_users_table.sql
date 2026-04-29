-- Migration: 0013_create_users_table.sql
-- Purpose:   Create users table as prerequisite for V1.1 user-scoped FK references
-- Idempotent: YES (CREATE TABLE/INDEX IF NOT EXISTS)

BEGIN;

-- Ensure trigger function exists (defined in infra/init.sql; redeclared here for standalone safety)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       TEXT        NOT NULL,
    name        TEXT,
    role        TEXT        NOT NULL DEFAULT 'user'
                            CHECK (role IN ('owner', 'admin', 'manager', 'user')),
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'disabled')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users(email);

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

COMMIT;
