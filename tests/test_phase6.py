"""Phase 6 Verification Tests."""
import os
import unittest
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.graph.engine import GraphEngine
from zero_drift.llm.registry import ModelRegistry
from zero_drift.llm.router import ModelRouter
from zero_drift.llm.stats import ModelStats
from zero_drift.execution.scope import ScopeEnforcer
from zero_drift.execution.executor import ToolExecutor
from zero_drift.events.log import EventLog
from zero_drift.agents.base import BaseAgent
from zero_drift.agents.roles import Architect, Implementer, Verifier
from zero_drift.orchestrator.engine import Orchestrator
from zero_drift.orchestrator.swarm import Swarm

class TestPhase6(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase6.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        
        self.graph = GraphEngine(self.db_path)
        self.registry = ModelRegistry("src/zero_drift/llm/providers.yaml")
        self.router = ModelRouter(self.registry)
        self.stats_path = "test_phase6_stats.json"
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)
        self.stats = ModelStats(self.stats_path)
        
        self.event_log = EventLog(self.conn)
        self.scope = ScopeEnforcer(["/tmp"])
        self.executor = ToolExecutor(self.event_log, self.scope)
        
    def tearDown(self):
        self.conn.close()
        self.cleanup_db()
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_agent_roles_and_creation(self):
        arch = Architect("A1", "Architect", self.router, self.executor, self.stats)
        impl = Implementer("I1", "Implementer", self.router, self.executor, self.stats)
        ver = Verifier("V1", "Verifier", self.router, self.executor, self.stats)
        
        self.assertEqual(arch.role, "Architect")
        self.assertEqual(impl.role, "Implementer")
        self.assertEqual(ver.role, "Verifier")

    def test_agent_think_records_stats_and_cost(self):
        agent = Implementer("I1", "Implementer", self.router, self.executor, self.stats)
        res = agent.think("Write code for feature X", {})
        self.assertIn("Implementer", res)
        
        # Check stats recorded (routes to cheap model due to small token estimate)
        agg = self.stats.get_stats("gpt-4o-mini") 
        self.assertGreater(agg.get("total_calls", 0), 0)
        self.assertGreater(agg.get("total_cost", 0.0), 0.0)

    def test_orchestrator_dependency_aware_execution(self):
        n1 = self.graph.add_node("Arch")
        n2 = self.graph.add_node("Impl")
        n3 = self.graph.add_node("Verify")
        self.graph.add_edge(n1, n2)
        self.graph.add_edge(n2, n3)
        
        agents = {
            n1: Architect("A1", "Architect", self.router, self.executor, self.stats),
            n2: Implementer("I1", "Implementer", self.router, self.executor, self.stats),
            n3: Verifier("V1", "Verifier", self.router, self.executor, self.stats)
        }
        swarm = Swarm(agents)
        orch = Orchestrator(self.graph, swarm)
        
        # Should execute in topological order without raising errors
        orch.plan_and_execute()

    def test_swarm_parallel_execution_safe(self):
        # Create independent nodes (same layer)
        n1 = self.graph.add_node("Task1")
        n2 = self.graph.add_node("Task2")
        
        agents = {
            n1: Implementer("I1", "Implementer", self.router, self.executor, self.stats),
            n2: Implementer("I2", "Implementer", self.router, self.executor, self.stats)
        }
        swarm = Swarm(agents)
        results = swarm.execute_layer([n1, n2])
        self.assertEqual(len(results), 2)
