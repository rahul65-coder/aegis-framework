"""Phase 10 Verification Tests."""
import os
import shutil
import tempfile
import unittest
from zero_drift.integration.runner import ZeroDriftRunner

class TestPhase10(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase10.db"
        self.workspace = tempfile.mkdtemp()
        self.cleanup_db()
        self.runner = ZeroDriftRunner(db_path=self.db_path, workspace_dir=self.workspace)

    def tearDown(self):
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
        self.cleanup_db()

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_end_to_end_integration(self):
        result = self.runner.run_prompt("Build a secure login feature")
        
        # Verify planning
        self.assertIsNotNone(result["plan"])
        self.assertTrue(len(result["nodes"]) > 0)
        
        # Verify execution & side effects
        feature_file = os.path.join(self.workspace, "feature.py")
        self.assertTrue(os.path.exists(feature_file))
        with open(feature_file, "r") as f:
            self.assertIn("implemented feature", f.read())
            
        # Verify Quality
        self.assertEqual(result["verify_status"], "VERIFIED")
        self.assertFalse(result["scope_drift"]) # No scope drift
        
        # Verify Cost tracking
        self.assertGreater(result["cost_spent"], 0.0)
        
    def test_ambiguity_blocks_execution(self):
        res = self.runner.run_prompt("Should we build maybe something?")
        self.assertEqual(res, "BLOCKED_AMBIGUITY")
        
    def test_budget_blocks_execution(self):
        # Exhaust budget
        self.runner.cost_mgr.spent = 10.0
        res = self.runner.run_prompt("Build another feature")
        self.assertEqual(res, "BLOCKED_BUDGET")
