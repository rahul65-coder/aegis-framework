"""Swarm - Parallel execution of independent tasks."""
import concurrent.futures

class Swarm:
    def __init__(self, agents_map: dict):
        # agents_map: node_id -> Agent instance
        self.agents_map = agents_map

    def execute_node(self, node_id):
        agent = self.agents_map.get(node_id)
        if agent:
            return agent.think(f"Execute node {node_id}", {})
        return None

    def execute_layer(self, layer_nodes):
        """Execute all nodes in a topological layer concurrently."""
        results = []
        # Parallelism only when safe (independent nodes in same layer)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.execute_node, nid) for nid in layer_nodes]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        return results
