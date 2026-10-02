"""ZeroDrift Integration Runner."""
import os
import tempfile
import shutil
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.graph.engine import GraphEngine
from zero_drift.events.log import EventLog
from zero_drift.state.manager import StateManager
from zero_drift.execution.scope import ScopeEnforcer
from zero_drift.execution.executor import ToolExecutor
from zero_drift.execution.file_ops import compute_hash
from zero_drift.llm.registry import ModelRegistry
from zero_drift.llm.router import ModelRouter
from zero_drift.llm.stats import ModelStats
from zero_drift.agents.roles import Implementer
from zero_drift.orchestrator.engine import Orchestrator
from zero_drift.orchestrator.swarm import Swarm
from zero_drift.quality.claims import Claim
from zero_drift.quality.verifier import Verifier
from zero_drift.quality.drift_guard import DriftGuard
from zero_drift.planning.task_engine import TaskEngine
from zero_drift.planning.planner import Planner
from zero_drift.planning.estimator import Estimator
from zero_drift.planning.approval import ApprovalSystem
from zero_drift.planning.cost_manager import CostManager
from zero_drift.planning.budget import Budget
from zero_drift.recovery.recovery import RecoveryEngine

class ZeroDriftRunner:
    def __init__(self, db_path="aegis_zero.db", workspace_dir=None):
        self.db_path = db_path
        self.conn = get_connection(db_path)
        run_migrations(self.conn)
        
        self.workspace_dir = workspace_dir or tempfile.mkdtemp()
        
        # Core systems
        self.graph = GraphEngine(self.db_path)
        self.event_log = EventLog(self.conn)
        self.state_mgr = StateManager(self.conn)
        
        # Execution
        self.scope = ScopeEnforcer([self.workspace_dir])
        self.executor = ToolExecutor(self.event_log, self.scope)
        
        # LLM
        self.registry = ModelRegistry("src/zero_drift/llm/providers.yaml")
        self.router = ModelRouter(self.registry)
        self.stats = ModelStats()
        
        # Quality
        self.verifier = Verifier()
        self.drift_guard = DriftGuard([self.workspace_dir])
        
        # Planning
        self.task_engine = TaskEngine()
        self.planner = Planner()
        self.estimator = Estimator()
        self.approval = ApprovalSystem()
        self.budget = Budget(limit=10.0)
        self.cost_mgr = CostManager()
        
        # Recovery
        self.recovery = RecoveryEngine(self.event_log, self.state_mgr)
        
    def run_prompt(self, prompt: str):
        # 1. Objective Lock
        lock = self.task_engine.lock_objective(prompt)
        
        # 2. Planning & Ambiguity Check
        if self.planner.handle_ambiguity(prompt) == "APPROVAL_REQUIRED":
            return "BLOCKED_AMBIGUITY"
            
        tasks = self.task_engine.decompose_prompt(prompt)
        plan = self.planner.generate_plan(tasks)
        estimate = self.estimator.estimate(plan)
        
        # 3. Budget Pre-call Check
        if not self.cost_mgr.pre_call_check(estimate["cost"], self.budget):
            return "BLOCKED_BUDGET"
            
        # 4. Approval (Simulate user granting approval for integration test)
        # In real scenario, this waits for user input. Here we simulate it.
        
        # 5. Graph Construction
        nodes = []
        for task in tasks:
            nid = self.graph.add_node(task, content=task)
            nodes.append(nid)
            
        # 6. Agent Swarm Execution
        agents = {nid: Implementer(f"agent_{nid}", "Implementer", self.router, self.executor, self.stats) for nid in nodes}
        swarm = Swarm(agents)
        orch = Orchestrator(self.graph, swarm)
        orch.plan_and_execute()
        
        # 7. Side Effect Execution (File Edit + Git Commit)
        target_file = os.path.join(self.workspace_dir, "feature.py")
        with open(target_file, "w") as f:
            f.write("# initial\n")
            
        expected_hash = compute_hash(target_file)
        self.executor.execute_file_edit(
            agent_id="agent_1",
            file_path=target_file,
            expected_hash=expected_hash,
            new_content="# implemented feature\n",
            idempotency_key="edit_feature"
        )
        
        # 8. Verification & Drift Guard
        claim = Claim("Feature implemented", evidence={"source": "pytest", "passed": True})
        verify_status = self.verifier.verify(claim)
        
        scope_drift = self.drift_guard.detect_scope_drift([target_file])
        
        # 9. Cost Recording
        self.cost_mgr.record_usage(estimate["cost"])
        
        # 10. Checkpoint
        cp_id = self.state_mgr.create_checkpoint("PHASE_10", {"nodes": nodes})
        self.state_mgr.verify_checkpoint(cp_id)
        
        return {
            "objective_hash": lock.hash,
            "plan": plan,
            "nodes": nodes,
            "verify_status": verify_status,
            "scope_drift": scope_drift,
            "cost_spent": self.cost_mgr.spent
        }
