"""Phase 2 Verification Tests."""
import os
import unittest
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.graph.engine import GraphEngine

class TestGraphEngine(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase2.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        self.engine = GraphEngine(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.cleanup_db()

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_node_crud(self):
        nid = self.engine.add_node("task_1", content="hello")
        node = self.engine.get_node(nid)
        self.assertEqual(node["name"], "task_1")
        self.assertEqual(node["status"], "PENDING")
        
    def test_edge_crud(self):
        n1 = self.engine.add_node("task_a")
        n2 = self.engine.add_node("task_b")
        eid = self.engine.add_edge(n1, n2)
        self.assertGreater(eid, 0)
        deps = self.engine.get_dependencies(n2)
        self.assertIn(n1, deps)

    def test_status_transitions(self):
        nid = self.engine.add_node("task_trans")
        self.engine.update_status(nid, "IN_PROGRESS")
        node = self.engine.get_node(nid)
        self.assertEqual(node["status"], "IN_PROGRESS")
        
    def test_invalid_transition(self):
        nid = self.engine.add_node("task_inv")
        with self.assertRaises(ValueError):
            self.engine.update_status(nid, "VERIFIED")

    def test_hash_tracking_and_staleness(self):
        nid = self.engine.add_node("task_hash", content="v1")
        node = self.engine.get_node(nid)
        self.assertFalse(self.engine.check_staleness(nid, node["content_hash"]))
        
        self.engine.update_content(nid, "v2")
        self.assertTrue(self.engine.check_staleness(nid, node["content_hash"]))

    def test_topological_layers(self):
        n1 = self.engine.add_node("layer_1")
        n2 = self.engine.add_node("layer_2")
        n3 = self.engine.add_node("layer_3")
        self.engine.add_edge(n1, n2)
        self.engine.add_edge(n2, n3)
        
        layers = self.engine.get_topological_layers()
        self.assertEqual(layers[0], [n1])
        self.assertEqual(layers[1], [n2])
        self.assertEqual(layers[2], [n3])

    def test_context_slice(self):
        n1 = self.engine.add_node("ctx_1")
        n2 = self.engine.add_node("ctx_2")
        n3 = self.engine.add_node("ctx_3")
        self.engine.add_edge(n1, n2)
        self.engine.add_edge(n2, n3)
        
        ctx = self.engine.get_context_slice(n2, depth=1)
        self.assertIn(n1, ctx["nodes"])
        self.assertIn(n2, ctx["nodes"])
        self.assertIn(n3, ctx["nodes"])
