"""E-Commerce Application Builder & Validator using ZeroDrift Framework."""
import os
from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.graph.engine import GraphEngine
from zero_drift.events.log import EventLog
from zero_drift.state.manager import StateManager
from zero_drift.execution.scope import ScopeEnforcer
from zero_drift.execution.executor import ToolExecutor
from zero_drift.llm.registry import ModelRegistry
from zero_drift.llm.router import ModelRouter
from zero_drift.llm.stats import ModelStats
from zero_drift.agents.roles import Implementer
from zero_drift.orchestrator.engine import Orchestrator
from zero_drift.orchestrator.swarm import Swarm
from zero_drift.quality.drift_guard import DriftGuard
from zero_drift.quality.blast_radius import BlastRadiusCalculator

class EcommerceRunner:
    def __init__(self, workspace_dir):
        self.workspace_dir = workspace_dir
        self.db_path = os.path.join(workspace_dir, "ecommerce.db")
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        
        self.graph = GraphEngine(self.db_path)
        self.event_log = EventLog(self.conn)
        self.state_mgr = StateManager(self.conn)
        
        self.scope = ScopeEnforcer([workspace_dir])
        self.executor = ToolExecutor(self.event_log, self.scope)
        self.drift_guard = DriftGuard([workspace_dir])
        
        registry = ModelRegistry("src/zero_drift/llm/providers.yaml")
        router = ModelRouter(registry)
        stats = ModelStats(os.path.join(workspace_dir, "stats.json"))
        
        # 1. Planning & Graph Construction
        self.db_node = self.graph.add_node("setup_database")
        self.backend_node = self.graph.add_node("implement_backend")
        self.frontend_node = self.graph.add_node("implement_frontend")
        self.test_node = self.graph.add_node("run_tests")
        
        self.graph.add_edge(self.db_node, self.backend_node)
        self.graph.add_edge(self.backend_node, self.frontend_node)
        self.graph.add_edge(self.backend_node, self.test_node)
        self.graph.add_edge(self.frontend_node, self.test_node)
        
        # 2. Agents
        self.agents = {
            self.db_node: Implementer("DB_Agent", "Implementer", router, self.executor, stats),
            self.backend_node: Implementer("Backend_Agent", "Implementer", router, self.executor, stats),
            self.frontend_node: Implementer("Frontend_Agent", "Implementer", router, self.executor, stats),
            self.test_node: Implementer("Test_Agent", "Verifier", router, self.executor, stats)
        }
        
    def build_app(self):
        swarm = Swarm(self.agents)
        orch = Orchestrator(self.graph, swarm)
        
        # Execute Graph Layer by Layer (Simulating Swarm execution)
        self._create_db_schema()
        self._create_backend()
        self._create_frontend()
        self._create_tests()
        
        # Verify Drift Guard
        files_created = [
            os.path.join(self.workspace_dir, "app/main.py"),
            os.path.join(self.workspace_dir, "app/models.py"),
            os.path.join(self.workspace_dir, "app/routes.py"),
            os.path.join(self.workspace_dir, "frontend/index.html"),
            os.path.join(self.workspace_dir, "tests/test_api.py")
        ]
        
        is_drift = self.drift_guard.detect_scope_drift(files_created)
        
        # Calculate Blast Radius for backend changes
        blast_calc = BlastRadiusCalculator(self.graph)
        radius = blast_calc.calculate_blast_radius(self.backend_node)
        
        # Checkpoint state
        cp_id = self.state_mgr.create_checkpoint("ECOMMERCE_BUILD", {"nodes": [self.db_node, self.backend_node, self.frontend_node, self.test_node]})
        self.state_mgr.verify_checkpoint(cp_id)
        
        return {
            "drift_detected": is_drift,
            "blast_radius_of_backend": radius,
            "files": files_created,
            "checkpoint_id": cp_id
        }
        
    def _create_db_schema(self):
        file_path = os.path.join(self.workspace_dir, "app/models.py")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("""
import sqlite3
import os

DB_PATH = os.environ.get("ECOM_DB_PATH", "ecommerce.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    conn.execute("INSERT OR IGNORE INTO products (id, name, price, stock) VALUES (1, 'Laptop', 999.99, 10)")
    conn.execute("INSERT OR IGNORE INTO products (id, name, price, stock) VALUES (2, 'Mouse', 25.50, 100)")
    conn.commit()
    conn.close()
""")

    def _create_backend(self):
        routes_path = os.path.join(self.workspace_dir, "app/routes.py")
        with open(routes_path, "w") as f:
            f.write("""
from fastapi import APIRouter, HTTPException
from .models import get_db

router = APIRouter()

@router.get("/products")
def list_products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(p) for p in products]

@router.post("/cart/add/{product_id}")
def add_to_cart(product_id: int):
    conn = get_db()
    prod = conn.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
    if not prod or prod["stock"] <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Out of stock")
    conn.execute("UPDATE products SET stock = stock - 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"status": "added"}
""")
        main_path = os.path.join(self.workspace_dir, "app/main.py")
        with open(main_path, "w") as f:
            f.write("""
from fastapi import FastAPI
from .models import init_db
from .routes import router

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def startup():
    init_db()
""")

    def _create_frontend(self):
        os.makedirs(os.path.join(self.workspace_dir, "frontend"), exist_ok=True)
        html_path = os.path.join(self.workspace_dir, "frontend/index.html")
        with open(html_path, "w") as f:
            f.write("<html><body><h1>AEGIS ZERO E-Commerce</h1><div id='products'></div></body></html>")

    def _create_tests(self):
        os.makedirs(os.path.join(self.workspace_dir, "tests"), exist_ok=True)
        test_path = os.path.join(self.workspace_dir, "tests/test_api.py")
        with open(test_path, "w") as f:
            f.write("""
import os
import pytest
from fastapi.testclient import TestClient
os.environ["ECOM_DB_PATH"] = "test_ecom.db"

if os.path.exists("test_ecom.db"): os.remove("test_ecom.db")

from app.main import app

@pytest.fixture
def client():
    # Context manager is required in modern FastAPI/Starlette to trigger startup events
    with TestClient(app) as test_client:
        yield test_client

def test_list_products(client):
    res = client.get("/products")
    assert res.status_code == 200
    assert len(res.json()) >= 2

def test_add_to_cart(client):
    res = client.post("/cart/add/1")
    assert res.status_code == 200
    assert res.json()["status"] == "added"
""")
