from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


_DURATION_RE = re.compile(
    r"^(?:in\s+)?(?P<qty>\d+)\s*(?P<unit>s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days)\b\s*(?P<text>.+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Reminder:
    id: int
    message: str
    due_at: str
    created_at: str
    delivered: bool


def parse_reminder(raw: str, *, now: datetime | None = None) -> tuple[datetime, str] | None:
    """Parse strings like 'in 10m stretch' or '5 minutes check oven'."""
    match = _DURATION_RE.match(raw.strip())
    if not match:
        return None
    qty = int(match.group("qty"))
    unit = match.group("unit").lower()
    text = match.group("text").strip()
    if not text:
        return None
    if unit.startswith("s"):
        delta = timedelta(seconds=qty)
    elif unit.startswith("m"):
        delta = timedelta(minutes=qty)
    elif unit.startswith("h"):
        delta = timedelta(hours=qty)
    else:
        delta = timedelta(days=qty)
    base = now or datetime.now(timezone.utc)
    return base + delta, text


class ReminderStore:
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
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def add(self, message: str, due_at: datetime) -> Reminder | None:
        if not self.enabled:
            return None
        created = datetime.now(timezone.utc).isoformat()
        due = due_at.astimezone(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO reminders(message, due_at, created_at, delivered) VALUES (?, ?, ?, 0)",
                (message, due, created),
            )
            return Reminder(cursor.lastrowid or 0, message, due, created, False)

    def list_pending(self) -> list[Reminder]:
        if not self.enabled:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, message, due_at, created_at, delivered FROM reminders WHERE delivered = 0 ORDER BY due_at"
            ).fetchall()
        return [
            Reminder(row["id"], row["message"], row["due_at"], row["created_at"], bool(row["delivered"]))
            for row in rows
        ]

    def due_now(self, *, now: datetime | None = None) -> list[Reminder]:
        if not self.enabled:
            return []
        stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, message, due_at, created_at, delivered FROM reminders
                WHERE delivered = 0 AND due_at <= ?
                ORDER BY due_at
                """,
                (stamp,),
            ).fetchall()
        return [
            Reminder(row["id"], row["message"], row["due_at"], row["created_at"], bool(row["delivered"]))
            for row in rows
        ]

    def mark_delivered(self, reminder_id: int) -> bool:
        if not self.enabled:
            return False
        with self._connect() as conn:
            cursor = conn.execute("UPDATE reminders SET delivered = 1 WHERE id = ?", (reminder_id,))
            return cursor.rowcount > 0

    def cancel(self, reminder_id: int) -> bool:
        if not self.enabled:
            return False
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            return cursor.rowcount > 0
