"""Phase 7 Verification Tests."""
import os
import unittest
from zero_drift.quality.claims import Claim, is_agent_self_claim_sufficient
from zero_drift.quality.verifier import Verifier
from zero_drift.quality.drift_guard import DriftGuard
from zero_drift.quality.blast_radius import BlastRadiusCalculator
from zero_drift.graph.engine import GraphEngine
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations

class TestPhase7(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase7.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        self.graph = GraphEngine(self.db_path)
        self.verifier = Verifier()
        self.drift_guard = DriftGuard(["/tmp/project"])

    def tearDown(self):
        self.conn.close()
        self.cleanup_db()

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_unknown_not_true(self):
        claim = Claim("Task is done") # No evidence
        self.assertEqual(claim.validate(), "UNKNOWN")
        self.assertNotEqual(claim.validate(), "TRUE")
        self.assertNotEqual(claim.validate(), "VERIFIED")

    def test_agent_self_claim_not_evidence(self):
        claim = Claim("I did it", evidence={"source": "agent_self"})
        self.assertFalse(is_agent_self_claim_sufficient(claim))
        
        claim_valid = Claim("I did it", evidence={"source": "pytest", "passed": True})
        self.assertTrue(is_agent_self_claim_sufficient(claim_valid))

    def test_failed_evidence_not_verified(self):
        claim = Claim("Task done", evidence={"source": "pytest", "passed": False})
        res = self.verifier.verify(claim)
        self.assertNotEqual(res, "VERIFIED")
        self.assertEqual(res, "FAILED")

    def test_scope_drift_detected(self):
        # Allowed scope is /tmp/project
        is_drift = self.drift_guard.detect_scope_drift(["/tmp/project/src/main.py", "/etc/passwd"])
        self.assertTrue(is_drift)
        
        is_drift = self.drift_guard.detect_scope_drift(["/tmp/project/src/main.py"])
        self.assertFalse(is_drift)

    def test_unrelated_modification_detected(self):
        is_unrelated = self.drift_guard.detect_unrelated_modification(
            "/tmp/project/src/feature.py", 
            ["/tmp/project/src/feature.py", "/tmp/project/src/unrelated.py"]
        )
        self.assertTrue(is_unrelated)

    def test_blast_radius_and_targeted_tests(self):
        n1 = self.graph.add_node("core")
        n2 = self.graph.add_node("ui")
        n3 = self.graph.add_node("api")
        self.graph.add_edge(n1, n2)
        self.graph.add_edge(n1, n3)
        
        calc = BlastRadiusCalculator(self.graph)
        radius = calc.calculate_blast_radius(n1)
        self.assertIn(n2, radius)
        self.assertIn(n3, radius)
        
        tests = calc.select_targeted_tests([n1])
        self.assertIn(f"test_node_{n1}.py", tests)
        self.assertIn(f"test_node_{n2}.py", tests)
        self.assertIn(f"test_node_{n3}.py", tests)

    def test_verified_nodes_protected(self):
        protected = self.verifier.protect_verified_node("VERIFIED", {"passed": False})
        self.assertFalse(protected)
        
        allowed = self.verifier.protect_verified_node("VERIFIED", {"passed": True, "force_override": True})
        self.assertTrue(allowed)
