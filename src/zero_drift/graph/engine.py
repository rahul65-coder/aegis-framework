"""Graph Engine Core Implementation."""
import hashlib
from typing import List
from zero_drift.db.connection import get_connection
from .models import VALID_TRANSITIONS

class GraphEngine:
    def __init__(self, db_path: str = "aegis_zero.db"):
        self.db_path = db_path
        self.conn = get_connection(db_path)
        
    def add_node(self, name: str, node_type: str = "TASK", content: str = "") -> int:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cursor = self.conn.execute(
            "INSERT INTO nodes (name, status, content_hash) VALUES (?, ?, ?)",
            (name, "PENDING", content_hash)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_node(self, node_id: int) -> dict:
        cursor = self.conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Node {node_id} not found")
        return dict(row)

    def update_status(self, node_id: int, new_status: str):
        node = self.get_node(node_id)
        current_status = node["status"]
        
        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise ValueError(f"Invalid transition from {current_status} to {new_status}")
            
        self.conn.execute(
            "UPDATE nodes SET status = ? WHERE id = ?",
            (new_status, node_id)
        )
        self.conn.commit()

    def update_content(self, node_id: int, new_content: str):
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()
        # Content change resets status to PENDING to force reverification
        self.conn.execute(
            "UPDATE nodes SET content_hash = ?, status = 'PENDING' WHERE id = ?",
            (new_hash, node_id)
        )
        self.conn.commit()

    def check_staleness(self, node_id: int, expected_hash: str) -> bool:
        node = self.get_node(node_id)
        return node["content_hash"] != expected_hash

    def add_edge(self, source_id: int, target_id: int, relation_type: str = "DEPENDS_ON") -> int:
        if source_id == target_id:
            raise ValueError("Self loops not allowed")
        
        self.get_node(source_id)
        self.get_node(target_id)
        
        cursor = self.conn.execute(
            "INSERT INTO edges (source_id, target_id, relation_type) VALUES (?, ?, ?)",
            (source_id, target_id, relation_type)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_dependencies(self, node_id: int) -> List[int]:
        cursor = self.conn.execute(
            "SELECT source_id FROM edges WHERE target_id = ?", (node_id,)
        )
        return [row["source_id"] for row in cursor.fetchall()]

    def get_dependents(self, node_id: int) -> List[int]:
        cursor = self.conn.execute(
            "SELECT target_id FROM edges WHERE source_id = ?", (node_id,)
        )
        return [row["target_id"] for row in cursor.fetchall()]

    def get_context_slice(self, root_id: int, depth: int = 2) -> dict:
        visited_nodes = set()
        visited_edges = set()
        queue = [(root_id, 0)]
        
        while queue:
            curr_id, curr_depth = queue.pop(0)
            if curr_id in visited_nodes or curr_depth > depth:
                continue
            
            visited_nodes.add(curr_id)
            
            deps = self.get_dependencies(curr_id)
            for dep in deps:
                visited_edges.add((dep, curr_id))
                queue.append((dep, curr_depth + 1))
                
            dependents = self.get_dependents(curr_id)
            for dep in dependents:
                visited_edges.add((curr_id, dep))
                queue.append((dep, curr_depth + 1))
                
        return {
            "nodes": list(visited_nodes),
            "edges": list(visited_edges)
        }

    def get_topological_layers(self) -> List[List[int]]:
        in_degree = {}
        adj = {}
        nodes = []
        
        cursor = self.conn.execute("SELECT id FROM nodes")
        for row in cursor.fetchall():
            nid = row["id"]
            nodes.append(nid)
            in_degree[nid] = 0
            adj[nid] = []
            
        cursor = self.conn.execute("SELECT source_id, target_id FROM edges")
        for row in cursor.fetchall():
            src = row["source_id"]
            tgt = row["target_id"]
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1
            
        queue = [n for n in nodes if in_degree[n] == 0]
        layers = []
        
        while queue:
            layers.append(sorted(queue)) # Sort for deterministic output
            next_queue = []
            for n in queue:
                for neighbor in adj[n]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue
            
        if sum(len(l) for l in layers) != len(nodes):
            raise ValueError("Cycle detected in graph")
            
        return layers
