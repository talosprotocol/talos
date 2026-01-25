import sqlite3
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from tga.domain.models import ActionRequest, ExecutionLogEntry, ExecutionState, ArtifactType

class SqliteStore:
    """
    Hardened SQLite storage for TGA state and logs.
    Implements Phase 2 requirements (WAL, 0600 permissions, schema tracking).
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # 1. Enforce secure permissions (0600)
        if not os.path.exists(self.db_path):
            open(self.db_path, 'a').close()
            os.chmod(self.db_path, 0o600)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # 2. Enable WAL mode for concurrency and performance
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        # 3. Create tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                principal_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                key TEXT PRIMARY KEY,
                result_digest TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                trace_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                principal_id TEXT NOT NULL,
                ts TEXT NOT NULL,
                prev_entry_digest TEXT NOT NULL,
                entry_digest TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                artifact_digest TEXT NOT NULL,
                artifact_data TEXT,
                idempotency_key TEXT,
                PRIMARY KEY (trace_id, seq)
            )
        """)
        self.conn.commit()

    def save_session(self, session_id: uuid.UUID, principal_id: uuid.UUID):
        self.conn.execute(
            "INSERT INTO sessions (session_id, principal_id, created_at) VALUES (?, ?, ?)",
            (str(session_id), str(principal_id), datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def get_session(self, session_id: uuid.UUID) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM sessions WHERE session_id = ?", (str(session_id),)).fetchone()
        if row:
            return {"principal_id": uuid.UUID(row["principal_id"])}
        return None

    def check_idempotency(self, key: uuid.UUID) -> Optional[str]:
        row = self.conn.execute("SELECT result_digest FROM idempotency_keys WHERE key = ?", (str(key),)).fetchone()
        return row["result_digest"] if row else None

    def record_idempotency(self, key: uuid.UUID, result_digest: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO idempotency_keys (key, result_digest, created_at) VALUES (?, ?, ?)",
            (str(key), result_digest, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def append_log_entry(self, entry: ExecutionLogEntry):
        self.conn.execute(
            """INSERT INTO execution_logs 
               (trace_id, seq, principal_id, ts, prev_entry_digest, entry_digest, 
                from_state, to_state, artifact_type, artifact_id, artifact_digest, 
                artifact_data, idempotency_key) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(entry.trace_id), entry.seq, str(entry.principal_id), entry.ts.isoformat(),
                entry.prev_entry_digest, entry.entry_digest,
                entry.from_state, entry.to_state, entry.artifact_type,
                str(entry.artifact_id), entry.artifact_digest,
                json.dumps(entry.artifact_data) if entry.artifact_data else None,
                str(entry.idempotency_key) if entry.idempotency_key else None
            )
        )
        self.conn.commit()

    def get_execution_log(self, trace_id: uuid.UUID) -> List[ExecutionLogEntry]:
        rows = self.conn.execute(
            "SELECT * FROM execution_logs WHERE trace_id = ? ORDER BY seq ASC",
            (str(trace_id),)
        ).fetchall()
        
        entries = []
        for row in rows:
            entries.append(ExecutionLogEntry(
                trace_id=uuid.UUID(row["trace_id"]),
                principal_id=uuid.UUID(row["principal_id"]),
                seq=row["seq"],
                ts=datetime.fromisoformat(row["ts"]),
                prev_entry_digest=row["prev_entry_digest"],
                entry_digest=row["entry_digest"],
                from_state=ExecutionState(row["from_state"]),
                to_state=ExecutionState(row["to_state"]),
                artifact_type=ArtifactType(row["artifact_type"]),
                artifact_id=uuid.UUID(row["artifact_id"]),
                artifact_digest=row["artifact_digest"],
                artifact_data=json.loads(row["artifact_data"]) if row["artifact_data"] else None,
                idempotency_key=uuid.UUID(row["idempotency_key"]) if row["idempotency_key"] else None
            ))
        return entries

    def get_latest_log_entry(self, trace_id: uuid.UUID) -> Optional[ExecutionLogEntry]:
        log = self.get_execution_log(trace_id)
        return log[-1] if log else None
