"""Storage module for configuration service."""

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel  # type: ignore

from .validation import validate_and_normalize  # type: ignore


class ConfigDraft(BaseModel):  # type: ignore
    """Configuration draft model."""

    draft_id: str
    principal: str
    config_digest: str
    config_json: str  # Stored as JSON string
    note: str | None
    created_at: datetime


class ConfigHistory(BaseModel):  # type: ignore
    """Configuration history model."""

    id: str  # active_config_id
    draft_id: str
    config_digest: str
    config_json: str
    created_at: datetime
    principal: str | None = None


class IdempotencyRecord(BaseModel):  # type: ignore
    """Idempotency record model."""

    key: str
    principal: str
    method: str
    path: str
    request_digest: str
    response_code: int
    response_body: str
    created_at: datetime


# Simple SQLite adapter for v1
class Database:
    """SQLite database adapter for Talos configuration service."""

    def __init__(self, db_path: str = "talos_config.db"):
        """Initialize database connection and schema.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()

        # Drafts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                draft_id TEXT PRIMARY KEY,
                principal TEXT NOT NULL,
                config_digest TEXT NOT NULL,
                config_json TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # History (Active Configs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                draft_id TEXT NOT NULL,
                config_digest TEXT NOT NULL,
                config_json TEXT NOT NULL,
                principal TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Current Head Pointer (Singleton)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_head (
                lock_id INTEGER PRIMARY KEY CHECK (lock_id = 1),
                history_id TEXT NOT NULL,
                FOREIGN KEY(history_id) REFERENCES history(id)
            )
        """)

        # Idempotency
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS idempotency (
                key TEXT NOT NULL,
                principal TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                request_digest TEXT NOT NULL,
                response_code INTEGER NOT NULL,
                response_body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (key, principal, method, path)
            )
        """)

        self.conn.commit()
        self._seed_minimal()

    def _seed_minimal(self) -> None:
        """Seed the database with a minimal configuration if empty."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history")
        if cursor.fetchone()[0] == 0:
            # Imports moved to top

            minimal_config = {
                "config_version": "1.0",
                "global": {
                    "env": "local",
                    "region": "us-east-1",
                    "log_level": "INFO",
                },
                "gateway": {
                    "port": 8000,
                    "host": "0.0.0.0",  # nosec: B104 (intended for container)
                    "disable_auth": True,
                },
                "audit": {"storage_backend": "memory", "retention_days": 1},
                "mcp_connector": {"allowed_servers": []},
            }

            result = validate_and_normalize(minimal_config, strict=True)
            if result.valid:
                config_id = str(uuid.uuid4())
                draft_id = "initial-bootstrap-draft"
                created_at = datetime.now(UTC).isoformat()

                cursor.execute(
                    (
                        "INSERT INTO history "
                        "(id, draft_id, config_digest, config_json, "
                        "principal, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        config_id,
                        draft_id,
                        result.digest,
                        json.dumps(result.normalized_config),
                        "SYSTEM",
                        created_at,
                    ),
                )
                cursor.execute(
                    "INSERT OR REPLACE INTO current_head "
                    "(lock_id, history_id) "
                    "VALUES (1, ?)",
                    (config_id,),
                )
                self.conn.commit()

    def get_current_config(self) -> ConfigHistory | None:
        """Retrieve the currently active configuration.

        Returns:
            ConfigHistory | None: The active config history record or None.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT h.id, h.draft_id, h.config_digest, h.config_json,
                   h.created_at, h.principal
            FROM current_head c
            JOIN history h ON c.history_id = h.id
            WHERE c.lock_id = 1
        """)
        row = cursor.fetchone()
        if row:
            return ConfigHistory(
                id=row[0],
                draft_id=row[1],
                config_digest=row[2],
                config_json=row[3],
                created_at=datetime.fromisoformat(row[4]),
                principal=row[5],
            )
        return None

    def save_draft(self, draft: ConfigDraft) -> None:
        """Save a new configuration draft.

        Args:
            draft: The ConfigDraft object to persist.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            (
                "INSERT INTO drafts "
                "(draft_id, principal, config_digest, config_json, "
                "note, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            ),
            (
                draft.draft_id,
                draft.principal,
                draft.config_digest,
                draft.config_json,
                draft.note,
                draft.created_at.isoformat(),
            ),
        )
        self.conn.commit()

    def get_draft(self, draft_id: str) -> ConfigDraft | None:
        """Retrieve a specific configuration draft.

        Args:
            draft_id: The ID of the draft to retrieve.

        Returns:
            ConfigDraft | None: The draft or None if not found.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT draft_id, principal, config_digest, config_json, "
            "note, created_at "
            "FROM drafts WHERE draft_id = ?",
            (draft_id,),
        )
        row = cursor.fetchone()
        if row:
            return ConfigDraft(
                draft_id=row[0],
                principal=row[1],
                config_digest=row[2],
                config_json=row[3],
                note=row[4],
                created_at=datetime.fromisoformat(row[5]),
            )
        return None

    def publish_draft(self, history: ConfigHistory) -> None:
        """Publish a draft by adding it to history and updating current head.

        Args:
            history: The ConfigHistory record representing the
                published config.
        """
        cursor = self.conn.cursor()

        # Insert History Record
        cursor.execute(
            "INSERT INTO history (id, draft_id, config_digest, "
            "config_json, principal, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                history.id,
                history.draft_id,
                history.config_digest,
                history.config_json,
                history.principal,
                history.created_at.isoformat(),
            ),
        )

        # Update Head
        cursor.execute(
            "INSERT OR REPLACE INTO current_head (lock_id, history_id) "
            "VALUES (1, ?)",
            (history.id,),
        )

        self.conn.commit()

    def list_history(
        self,
        limit: int,
        before_created_at: datetime | None,
        before_id: str | None,
    ) -> list[ConfigHistory]:
        """List configuration history with pagination.

        Args:
            limit: Maximum number of records to return.
            before_created_at: Pagination cursor (timestamp).
            before_id: Pagination cursor (ID tie-break).

        Returns:
            list[ConfigHistory]: List of history records.
        """
        cursor = self.conn.cursor()
        query = (
            "SELECT id, draft_id, config_digest, config_json, "
            "created_at, principal FROM history"
        )
        params: list[Any] = []

        if before_created_at and before_id:
            # Cursor Logic: (created_at, id) tuple comparison for DESC order
            # created_at < cursor_time OR
            # (created_at = cursor_time AND id < cursor_id)
            query += " WHERE (created_at < ?) OR (created_at = ? AND id < ?)"
            params.extend(
                [
                    before_created_at.isoformat(),
                    before_created_at.isoformat(),
                    before_id,
                ]
            )

        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        return [
            ConfigHistory(
                id=r[0],
                draft_id=r[1],
                config_digest=r[2],
                config_json=r[3],
                created_at=datetime.fromisoformat(r[4]),
                principal=r[5],
            )
            for r in rows
        ]

    def get_idempotency_record(
        self, key: str, principal: str, method: str, path: str
    ) -> IdempotencyRecord | None:
        """Retrieve an idempotency record.

        Args:
            key: The idempotency key.
            principal: The principal ID.
            method: The HTTP method.
            path: The API path.

        Returns:
            IdempotencyRecord | None: The record or None.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT key, principal, method, path, request_digest, "
            "response_code, response_body, created_at FROM idempotency "
            "WHERE key=? AND principal=? AND method=? AND path=?",
            (key, principal, method, path),
        )
        row = cursor.fetchone()
        if row:
            return IdempotencyRecord(
                key=row[0],
                principal=row[1],
                method=row[2],
                path=row[3],
                request_digest=row[4],
                response_code=row[5],
                response_body=row[6],
                created_at=datetime.fromisoformat(row[7]),
            )
        return None

    def save_idempotency_record(self, record: IdempotencyRecord) -> None:
        """Save a new idempotency record.

        Args:
            record: The IdempotencyRecord object to persist.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO idempotency (key, principal, method, path, "
            "request_digest, response_code, response_body, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.key,
                record.principal,
                record.method,
                record.path,
                record.request_digest,
                record.response_code,
                record.response_body,
                record.created_at.isoformat(),
            ),
        )
        self.conn.commit()
