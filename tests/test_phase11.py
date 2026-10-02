"""Phase 11 Real API Verification Tests."""
import os
import unittest
import requests
from zero_drift.llm.gemini_provider import RealGeminiProvider
from zero_drift.llm.registry import ModelRegistry
from zero_drift.llm.stats import ModelStats, CostCalculator

class TestPhase11RealAPI(unittest.TestCase):
    def setUp(self):
        self.registry = ModelRegistry("src/zero_drift/llm/providers.yaml")
        self.stats_path = "test_phase11_stats.json"
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)
        self.stats = ModelStats(self.stats_path)
        self.provider = None
        self.model_id = "gemini-2.5-flash"
        
        if os.environ.get("GEMINI_API_KEY"):
            self.provider = RealGeminiProvider(self.model_id)
        else:
            self.fail("GEMINI_API_KEY not found in environment. Phase 11 requires a real API key.")

    def tearDown(self):
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)

    def test_real_api_call_and_token_accounting(self):
        prompt = "Respond with exactly: AEGIS ZERO REAL API VERIFIED"
        result = self.provider.call(prompt)
        
        # Real response captured
        self.assertIn("AEGIS ZERO REAL API VERIFIED", result["content"])
        self.assertGreater(result["input_tokens"], 0)
        self.assertGreaterEqual(result["output_tokens"], 0)
        
        model_config = self.registry.get_model_by_id(self.model_id)
        cost = CostCalculator.calculate_cost(model_config, result["input_tokens"], result["output_tokens"])
        
        self.stats.record_call(self.model_id, "v1", result["input_tokens"], result["output_tokens"], cost)
        
        agg = self.stats.get_stats(self.model_id)
        self.assertEqual(agg["total_calls"], 1)
        self.assertGreater(agg["total_input_tokens"], 0)
        self.assertGreater(agg["total_cost"], 0.0)

    def test_real_api_failure_handling(self):
        bad_provider = RealGeminiProvider("gemini-non-existent-model-xyz-123")
        with self.assertRaises(requests.exceptions.HTTPError):
            bad_provider.call("This should fail and raise HTTPError")
