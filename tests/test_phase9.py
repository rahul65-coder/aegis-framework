"""Phase 9 Verification Tests."""
import os
import unittest
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.events.log import EventLog
from zero_drift.state.manager import StateManager
from zero_drift.recovery.classifier import ErrorClassifier
from zero_drift.recovery.recovery import RecoveryEngine
from zero_drift.recovery.resume import ResumeSystem

class TestPhase9(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase9.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        
        self.event_log = EventLog(self.conn)
        self.state_mgr = StateManager(self.conn)
        self.recovery = RecoveryEngine(self.event_log, self.state_mgr)
        self.resume = ResumeSystem(self.recovery)

    def tearDown(self):
        self.conn.close()
        self.cleanup_db()

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_error_classifier_transient(self):
        classifier = ErrorClassifier()
        self.assertEqual(classifier.classify("Network timeout occurred"), "TRANSIENT")
        self.assertEqual(classifier.classify("API rate limit exceeded"), "TRANSIENT")

    def test_error_classifier_permanent(self):
        classifier = ErrorClassifier()
        self.assertEqual(classifier.classify("Permission denied"), "PERMANENT")
        self.assertEqual(classifier.classify("unauthorized access"), "PERMANENT")

    def test_error_classifier_crash(self):
        classifier = ErrorClassifier()
        self.assertEqual(classifier.classify("Process kill -9"), "CRASH")
        self.assertEqual(classifier.classify("Segmentation fault (core dumped)"), "CRASH")

    def test_recovery_inspects_event_log_and_does_not_repeat_blindly(self):
        # Log an intent and result (completed)
        intent_id1 = self.event_log.log_intent("key_completed", {"action": "edit"})
        self.event_log.log_result(intent_id1, {"status": "success"})
        
        # Log an intent without result (incomplete/crash)
        intent_id2 = self.event_log.log_intent("key_crashed", {"action": "edit2"})
        
        # Create an unverified checkpoint (partial action)
        self.state_mgr.create_checkpoint("PHASE_9", {"node": 5})
        
        recovered = self.recovery.recover_incomplete_actions()
        
        # Should recover the crashed one
        self.assertIn("key_crashed", recovered["actions_to_recover"])
        # Should NOT blindly repeat the completed one
        self.assertNotIn("key_completed", recovered["actions_to_recover"])
        
        # Should inspect partial checkpoint
        self.assertIsNotNone(recovered["partial_checkpoint"])

    def test_resume_system(self):
        self.event_log.log_intent("key_resume", {"action": "task"})
        
        res = self.resume.resume_session("session_123")
        self.assertEqual(res["status"], "RESUMED")
        self.assertIn("key_resume", res["recovered_actions"])
        
        # Resuming again shouldn't duplicate work
        res2 = self.resume.resume_session("session_123")
        self.assertEqual(res2, "ALREADY_RESUMED")
