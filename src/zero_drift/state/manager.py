"""State Manager & Checkpoints."""
import json
import sqlite3
from datetime import datetime, timezone

class StateManager:
    def __init__(self, conn):
        self.conn = conn
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                phase TEXT NOT NULL,
                state_data TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        self.conn.commit()

    def create_checkpoint(self, phase: str, state_data: dict, metadata: dict = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO checkpoints (timestamp, phase, state_data, is_verified, metadata) VALUES (?, ?, ?, 0, ?)",
            (datetime.now(timezone.utc).isoformat(), phase, json.dumps(state_data), json.dumps(metadata or {}))
        )
        self.conn.commit()
        return cursor.lastrowid

    def verify_checkpoint(self, checkpoint_id: int):
        self.conn.execute(
            "UPDATE checkpoints SET is_verified = 1 WHERE id = ?",
            (checkpoint_id,)
        )
        self.conn.commit()

    def get_latest_verified_checkpoint(self, phase: str = None):
        query = "SELECT * FROM checkpoints WHERE is_verified = 1"
        params = []
        if phase:
            query += " AND phase = ?"
            params.append(phase)
        query += " ORDER BY id DESC LIMIT 1"
        
        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)

    def detect_partial_actions(self):
        cursor = self.conn.execute("""
            SELECT * FROM checkpoints 
            WHERE is_verified = 0 
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_checkpoint(self, checkpoint_id: int):
        cursor = self.conn.execute("SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
