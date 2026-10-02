"""Orchestrator Engine - Dependency-aware execution."""
from zero_drift.graph.engine import GraphEngine
from .swarm import Swarm

class Orchestrator:
    def __init__(self, graph_engine: GraphEngine, swarm: Swarm):
        self.graph = graph_engine
        self.swarm = swarm

    def plan_and_execute(self):
        """Reads topological layers and executes layer by layer."""
        layers = self.graph.get_topological_layers()
        for layer in layers:
            self.swarm.execute_layer(layer)
