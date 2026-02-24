-- Personal Hub Template - Database Initialization
-- Creates tables for data items and sync state

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Data Items (Generic data storage for all sources)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS data_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR NOT NULL,                  -- whoop, apple_health, withings, spotify, google_calendar, etc.
    source_id VARCHAR NOT NULL,               -- Unique ID from the source system
    category VARCHAR NOT NULL,                -- health, music, calendar, etc.
    item_type VARCHAR NOT NULL,               -- recovery, workout, track, event, etc.
    title TEXT,
    content TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,       -- Source-specific data
    tags TEXT[] DEFAULT '{}'::text[],
    is_public BOOLEAN DEFAULT false,
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- When the item was created at source
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT now()  -- When we synced it
);

-- Unique constraint: one source_id per source
CREATE UNIQUE INDEX IF NOT EXISTS uq_source_source_id ON data_items (source, source_id);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_items_category ON data_items (category);
CREATE INDEX IF NOT EXISTS idx_items_source ON data_items (source);
CREATE INDEX IF NOT EXISTS idx_items_created ON data_items (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_metadata ON data_items USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_items_tags ON data_items USING gin (tags);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Sync State (Track sync status for each data source)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS sync_state (
    source VARCHAR PRIMARY KEY,               -- Source identifier (whoop, apple_health, etc.)
    last_sync_at TIMESTAMP WITH TIME ZONE,    -- Last successful sync
    next_sync_at TIMESTAMP WITH TIME ZONE,    -- Scheduled next sync
    cursor JSONB DEFAULT '{}'::jsonb,         -- Pagination cursor, last ID, etc.
    status VARCHAR DEFAULT 'idle',            -- idle, running, error
    error_message TEXT,
    items_synced INTEGER DEFAULT 0            -- Total items synced (lifetime)
);

-- Insert default sync state for all sources
INSERT INTO sync_state (source, status) VALUES
    ('whoop', 'idle'),
    ('apple_health', 'idle'),
    ('withings', 'idle'),
    ('spotify', 'idle'),
    ('google_calendar', 'idle')
ON CONFLICT (source) DO NOTHING;
