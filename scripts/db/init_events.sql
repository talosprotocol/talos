CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    schema_version TEXT,
    timestamp BIGINT,
    cursor TEXT UNIQUE,
    event_type TEXT,
    outcome TEXT,
    session_id TEXT,
    correlation_id TEXT,
    agent_id TEXT,
    peer_id TEXT,
    tool TEXT,
    method TEXT,
    resource TEXT,
    metadata JSONB,
    metrics JSONB,
    hashes JSONB,
    integrity JSONB,
    integrity_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_cursor ON events(cursor);
CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id);
