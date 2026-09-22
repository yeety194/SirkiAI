from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class MemoryItem:
    id: int
    key: str
    value: str
    created_at: str


class MemoryStore:
    """Opt-in persistent memory backed by SQLite."""

    def __init__(self, db_path: Path, *, enabled: bool) -> None:
        self.enabled = enabled
        self.db_path = db_path
        if enabled:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)")

    def remember(self, key: str, value: str) -> MemoryItem | None:
        if not self.enabled:
            return None
        created = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO memories(key, value, created_at) VALUES (?, ?, ?)",
                (key.strip(), value.strip(), created),
            )
            return MemoryItem(cursor.lastrowid or 0, key.strip(), value.strip(), created)

    def recall(self, query: str, limit: int = 10) -> list[MemoryItem]:
        if not self.enabled:
            return []
        like = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, key, value, created_at FROM memories
                WHERE key LIKE ? OR value LIKE ?
                ORDER BY id DESC LIMIT ?
                """,
                (like, like, limit),
            ).fetchall()
        return [MemoryItem(row["id"], row["key"], row["value"], row["created_at"]) for row in rows]

    def list_recent(self, limit: int = 20) -> list[MemoryItem]:
        if not self.enabled:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, key, value, created_at FROM memories ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [MemoryItem(row["id"], row["key"], row["value"], row["created_at"]) for row in rows]

    def forget(self, memory_id: int) -> bool:
        if not self.enabled:
            return False
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def context_block(self, limit: int = 8) -> str:
        items = self.list_recent(limit)
        if not items:
            return ""
        lines = [f"- ({item.id}) {item.key}: {item.value}" for item in items]
        return "Known memories:\n" + "\n".join(lines)
