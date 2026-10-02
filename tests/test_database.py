"""Phase 1 Verification Tests.
Must prove: SQLite opens, WAL enabled, FK enabled, transactions work, rollback works, schema loads.
"""
import os
import sqlite3
import unittest
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations

class TestDatabasePhase1(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase1.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)

    def tearDown(self):
        self.conn.close()
        self.cleanup_db()

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_sqlite_opens(self):
        self.assertIsInstance(self.conn, sqlite3.Connection)

    def test_wal_enabled(self):
        cursor = self.conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), "wal", "WAL mode is not enabled!")

    def test_foreign_keys_enabled(self):
        cursor = self.conn.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        self.assertEqual(fk_status, 1, "Foreign keys are not enabled!")

    def test_schema_loads(self):
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        self.assertIn("nodes", tables)
        self.assertIn("edges", tables)

    def test_transaction_commit(self):
        self.conn.execute("INSERT INTO nodes (name, status) VALUES (?, ?)", ("test_node", "ACTIVE"))
        self.conn.commit()
        cursor = self.conn.execute("SELECT count(*) FROM nodes WHERE name='test_node'")
        self.assertEqual(cursor.fetchone()[0], 1)

    def test_transaction_rollback(self):
        self.conn.execute("INSERT INTO nodes (name, status) VALUES (?, ?)", ("rollback_node", "PENDING"))
        self.conn.rollback()
        cursor = self.conn.execute("SELECT count(*) FROM nodes WHERE name='rollback_node'")
        self.assertEqual(cursor.fetchone()[0], 0)

    def test_foreign_key_enforcement(self):
        # Inserting an edge with non-existent node IDs must fail due to FK constraint
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO edges (source_id, target_id, relation_type) VALUES (?, ?, ?)", 
                (999, 999, "LINK")
            )

if __name__ == "__main__":
    unittest.main()
