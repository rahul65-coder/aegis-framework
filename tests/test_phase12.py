"""Phase 12 E-Commerce Validation Tests."""
import os
import sys
import shutil
import subprocess
import unittest
from zero_drift.integration.ecommerce_runner import EcommerceRunner

class TestPhase12(unittest.TestCase):
    def setUp(self):
        self.workspace = "test_ecom_workspace"
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
        os.makedirs(self.workspace)
        self.runner = EcommerceRunner(self.workspace)

    def tearDown(self):
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)

    def test_ecommerce_build_and_verify(self):
        result = self.runner.build_app()
        
        # Verify files created
        for f in result["files"]:
            self.assertTrue(os.path.exists(f), f"Missing file: {f}")
            
        # Verify No Drift
        self.assertFalse(result["drift_detected"])
        
        # Verify Blast Radius (Test node depends on Backend node)
        self.assertIn(self.runner.test_node, result["blast_radius_of_backend"])
        
        # Run the actual e-commerce tests using subprocess
        # Use sys.executable to ensure we use the pytest installed in the active venv
        env = os.environ.copy()
        env["PYTHONPATH"] = self.workspace
        
        test_res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_api.py", "-v"],
            cwd=self.workspace,
            env=env,
            capture_output=True,
            text=True
        )
        
        self.assertEqual(test_res.returncode, 0, msg=f"E-commerce tests failed:\n{test_res.stdout}\n{test_res.stderr}")
