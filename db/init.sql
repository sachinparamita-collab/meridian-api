-- Users table
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255),
    api_key     VARCHAR(64) UNIQUE NOT NULL,
    tier        VARCHAR(20) NOT NULL DEFAULT 'trial',
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    endpoint        VARCHAR(100) NOT NULL,
    request_preview TEXT,
    response_ms     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed one test user
INSERT INTO users (email, name, api_key, tier)
VALUES ('test@meridian.com', 'Test User', 'mk_test_1234567890abcdef', 'trial')
ON CONFLICT DO NOTHING;