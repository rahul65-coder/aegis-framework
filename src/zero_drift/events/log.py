"""Event Log Engine - Append Only."""
import json
import sqlite3
from datetime import datetime, timezone

class EventLog:
    def __init__(self, conn):
        self.conn = conn
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                idempotency_key TEXT UNIQUE,
                payload TEXT,
                intent_id INTEGER
            )
        """)
        self.conn.commit()

    def log_intent(self, idempotency_key: str, payload: dict) -> int:
        cursor = self.conn.execute(
            "SELECT id FROM events WHERE idempotency_key = ?", 
            (idempotency_key,)
        )
        if cursor.fetchone():
            raise ValueError(f"Duplicate intent: {idempotency_key}")
        
        cursor = self.conn.execute(
            "INSERT INTO events (timestamp, event_type, idempotency_key, payload) VALUES (?, 'INTENT', ?, ?)",
            (datetime.now(timezone.utc).isoformat(), idempotency_key, json.dumps(payload))
        )
        self.conn.commit()
        return cursor.lastrowid

    def log_result(self, intent_id: int, payload: dict):
        self.conn.execute(
            "INSERT INTO events (timestamp, event_type, intent_id, payload) VALUES (?, 'RESULT', ?, ?)",
            (datetime.now(timezone.utc).isoformat(), intent_id, json.dumps(payload))
        )
        self.conn.commit()

    def log_failure(self, intent_id: int, payload: dict):
        self.conn.execute(
            "INSERT INTO events (timestamp, event_type, intent_id, payload) VALUES (?, 'FAILURE', ?, ?)",
            (datetime.now(timezone.utc).isoformat(), intent_id, json.dumps(payload))
        )
        self.conn.commit()

    def get_incomplete_events(self):
        cursor = self.conn.execute("""
            SELECT id, idempotency_key, payload 
            FROM events
            WHERE event_type = 'INTENT'
            AND id NOT IN (
                SELECT intent_id FROM events 
                WHERE intent_id IS NOT NULL 
                AND event_type IN ('RESULT', 'FAILURE')
            )
        """)
        return [dict(row) for row in cursor.fetchall()]
