"""Phase 8 Verification Tests."""
import unittest
from zero_drift.planning.task_engine import TaskEngine
from zero_drift.planning.planner import Planner
from zero_drift.planning.estimator import Estimator
from zero_drift.planning.mode_selector import ModeSelector
from zero_drift.planning.approval import ApprovalSystem
from zero_drift.planning.cost_manager import CostManager
from zero_drift.planning.budget import Budget

class TestPhase8(unittest.TestCase):
    def setUp(self):
        self.task_engine = TaskEngine()
        self.planner = Planner()
        self.estimator = Estimator()
        self.mode_selector = ModeSelector()
        self.approval = ApprovalSystem()
        self.cost_mgr = CostManager()
        self.budget = Budget(limit=1.00)

    def test_prompt_decomposition(self):
        tasks = self.task_engine.decompose_prompt("Build a web app")
        self.assertEqual(len(tasks), 2)
        self.assertTrue(all("task_" in t for t in tasks))

    def test_objective_lock_is_immutable(self):
        lock = self.task_engine.lock_objective("Build feature X")
        self.assertTrue(lock.locked)
        self.assertEqual(lock.objective, "Build feature X")
        # Namedtuples are immutable in Python
        with self.assertRaises(AttributeError):
            lock.objective = "Changed objective"

    def test_ambiguity_causes_approval(self):
        res1 = self.planner.handle_ambiguity("Build the thing")
        self.assertEqual(res1, "CLEAR")
        
        res2 = self.planner.handle_ambiguity("Should we build the thing?")
        self.assertEqual(res2, "APPROVAL_REQUIRED")
        
        res3 = self.planner.handle_ambiguity("This is an ambiguous request")
        self.assertEqual(res3, "APPROVAL_REQUIRED")

    def test_plan_and_estimate_generation(self):
        tasks = self.task_engine.decompose_prompt("E-commerce site")
        plan = self.planner.generate_plan(tasks)
        self.assertEqual(plan["status"], "planned")
        
        estimate = self.estimator.estimate(plan)
        self.assertIn("tokens", estimate)
        self.assertIn("cost", estimate)
        self.assertGreater(estimate["cost"], 0)

    def test_mode_suggestion(self):
        mode_std = self.mode_selector.suggest_mode({"cost": 0.01, "tokens": 1000})
        self.assertEqual(mode_std, "STANDARD")
        
        mode_promax = self.mode_selector.suggest_mode({"cost": 0.10, "tokens": 10000})
        self.assertEqual(mode_promax, "PROMAX")

    def test_user_approval_gate_blocks_by_default(self):
        plan = {"steps": ["task1"]}
        estimate = {"cost": 0.05}
        
        # Gate blocks by default
        self.assertFalse(self.approval.request_approval(plan, estimate))
        
        # Explicit grant works
        self.assertTrue(self.approval.grant_approval(True))
        self.assertFalse(self.approval.grant_approval(False))

    def test_budget_pre_call_check_blocks_exceed(self):
        # Budget limit is 1.00
        self.assertTrue(self.cost_mgr.pre_call_check(0.50, self.budget))
        self.cost_mgr.record_usage(0.50)
        
        # Spent 0.50, trying to estimate 0.60 -> Total 1.10 > 1.00
        self.assertFalse(self.cost_mgr.pre_call_check(0.60, self.budget))
        
        # Trying to estimate 0.40 -> Total 0.90 <= 1.00
        self.assertTrue(self.cost_mgr.pre_call_check(0.40, self.budget))
