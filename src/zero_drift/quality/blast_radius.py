"""Blast Radius & Targeted Tests."""
from zero_drift.graph.engine import GraphEngine

class BlastRadiusCalculator:
    def __init__(self, graph_engine: GraphEngine):
        self.graph = graph_engine

    def calculate_blast_radius(self, node_id: int) -> list:
        # Nodes that depend on this node
        return self.graph.get_dependents(node_id)

    def select_targeted_tests(self, modified_nodes: list) -> list:
        # blast radius is calculated
        # targeted tests are selected
        tests = set()
        for nid in modified_nodes:
            dependents = self.calculate_blast_radius(nid)
            for dep in dependents:
                tests.add(f"test_node_{dep}.py")
            tests.add(f"test_node_{nid}.py")
        return sorted(list(tests))
