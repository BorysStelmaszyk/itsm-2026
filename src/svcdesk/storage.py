# ai-generated: 100% - Codex implemented SQLite persistence for the Lab 1 ticket model
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class TicketStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        path = Path(self.database_path)
        if self.database_path != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    reporter_name TEXT NOT NULL,
                    reporter_email TEXT,
                    reporter_vip INTEGER NOT NULL,
                    impact INTEGER NOT NULL,
                    urgency INTEGER NOT NULL,
                    priority TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    closed_at TEXT,
                    related_to TEXT,
                    ack_due_at TEXT NOT NULL,
                    resolve_due_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "reporter": {
                "name": row["reporter_name"],
                "email": row["reporter_email"],
                "vip": bool(row["reporter_vip"]),
            },
            "impact": row["impact"],
            "urgency": row["urgency"],
            "priority": row["priority"],
            "state": row["state"],
            "created_at": row["created_at"],
            "acknowledged_at": row["acknowledged_at"],
            "resolved_at": row["resolved_at"],
            "closed_at": row["closed_at"],
            "related_to": row["related_to"],
            "sla": {
                "ack_due_at": row["ack_due_at"],
                "resolve_due_at": row["resolve_due_at"],
            },
        }

    def insert(self, ticket: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tickets (
                    id, title, description, reporter_name, reporter_email, reporter_vip,
                    impact, urgency, priority, state, created_at, acknowledged_at,
                    resolved_at, closed_at, related_to, ack_due_at, resolve_due_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket["id"],
                    ticket["title"],
                    ticket["description"],
                    ticket["reporter"]["name"],
                    ticket["reporter"]["email"],
                    int(ticket["reporter"]["vip"]),
                    ticket["impact"],
                    ticket["urgency"],
                    ticket["priority"],
                    ticket["state"],
                    ticket["created_at"],
                    ticket["acknowledged_at"],
                    ticket["resolved_at"],
                    ticket["closed_at"],
                    ticket["related_to"],
                    ticket["sla"]["ack_due_at"],
                    ticket["sla"]["resolve_due_at"],
                ),
            )

    def get(self, ticket_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return self._from_row(row) if row is not None else None

    def list(self, state: str | None, priority: str | None) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[str] = []
        if state is not None:
            clauses.append("state = ?")
            parameters.append(state)
        if priority is not None:
            clauses.append("priority = ?")
            parameters.append(priority)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(f"SELECT * FROM tickets{where} ORDER BY rowid", parameters).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, ticket: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tickets
                SET state = ?, acknowledged_at = ?, resolved_at = ?, closed_at = ?
                WHERE id = ?
                """,
                (
                    ticket["state"],
                    ticket["acknowledged_at"],
                    ticket["resolved_at"],
                    ticket["closed_at"],
                    ticket["id"],
                ),
            )
