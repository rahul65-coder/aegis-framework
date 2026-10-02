"""Phase 3 Verification Tests."""
import os
import json
import unittest
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.events.log import EventLog
from zero_drift.state.manager import StateManager

class TestPhase3(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase3.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        self.event_log = EventLog(self.conn)
        self.state_mgr = StateManager(self.conn)

    def tearDown(self):
        self.conn.close()
        self.cleanup_db()

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_append_only_behavior(self):
        intent_id = self.event_log.log_intent("key_1", {"action": "test"})
        # Append-only strictly enforced: no update/delete methods exist
        with self.assertRaises(AttributeError):
            self.event_log.update_event(intent_id, {})
        with self.assertRaises(AttributeError):
            self.event_log.delete_event(intent_id)

    def test_intent_before_action_and_pairing(self):
        intent_id = self.event_log.log_intent("key_pair", {"action": "create_node"})
        self.event_log.log_result(intent_id, {"status": "success"})
        
        incomplete = self.event_log.get_incomplete_events()
        self.assertEqual(len(incomplete), 0)

    def test_incomplete_event_detection(self):
        self.event_log.log_intent("key_incomplete", {"action": "create_edge"})
        incomplete = self.event_log.get_incomplete_events()
        self.assertEqual(len(incomplete), 1)
        self.assertEqual(incomplete[0]["idempotency_key"], "key_incomplete")

    def test_idempotency(self):
        self.event_log.log_intent("key_unique", {"action": "task_1"})
        with self.assertRaises(ValueError) as context:
            self.event_log.log_intent("key_unique", {"action": "task_1_duplicate"})
        self.assertIn("Duplicate intent", str(context.exception))

    def test_checkpoints_and_verification(self):
        cp_id = self.state_mgr.create_checkpoint("PHASE_3", {"graph_nodes": 5})
        
        latest = self.state_mgr.get_latest_verified_checkpoint("PHASE_3")
        self.assertIsNone(latest)
        
        self.state_mgr.verify_checkpoint(cp_id)
        latest = self.state_mgr.get_latest_verified_checkpoint("PHASE_3")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["id"], cp_id)

    def test_partial_action_detection(self):
        self.state_mgr.create_checkpoint("PHASE_3", {"graph_nodes": 6}, metadata={"step": "mid_execution"})
        
        partial = self.state_mgr.detect_partial_actions()
        self.assertIsNotNone(partial)
        self.assertEqual(partial["is_verified"], 0)

    def test_recovery_metadata(self):
        cp_id = self.state_mgr.create_checkpoint(
            "PHASE_3", 
            {"graph_nodes": 7}, 
            metadata={"last_success_node": 42, "resume_from": "step_5"}
        )
        
        cp = self.state_mgr.get_checkpoint(cp_id)
        metadata = json.loads(cp["metadata"])
        self.assertEqual(metadata["last_success_node"], 42)
