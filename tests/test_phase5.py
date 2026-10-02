"""Phase 5 Verification Tests."""
import os
import json
import unittest
from zero_drift.llm.registry import ModelRegistry
from zero_drift.llm.router import ModelRouter
from zero_drift.llm.stats import TokenCounter, CostCalculator, ModelStats
from zero_drift.llm.providers import ProviderAdapter

class TestPhase5(unittest.TestCase):
    def setUp(self):
        self.registry = ModelRegistry("src/zero_drift/llm/providers.yaml")
        self.router = ModelRouter(self.registry)
        self.stats_path = "test_model_stats.json"
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)
        self.stats = ModelStats(self.stats_path)

    def tearDown(self):
        if os.path.exists(self.stats_path):
            os.remove(self.stats_path)

    def test_provider_loading_and_registration(self):
        models = self.registry.models
        self.assertGreater(len(models), 0)
        providers = set(m["provider"] for m in models)
        self.assertIn("openai", providers)
        self.assertIn("anthropic", providers)

    def test_hard_capability_and_context_window_filters(self):
        models = self.registry.get_models(required_capabilities=["vision"], min_context_window=150000)
        self.assertEqual(len(models), 1) # Only claude-3-5-sonnet has vision and >150k context in our dummy yaml
        self.assertEqual(models[0]["id"], "claude-3-5-sonnet-20240620")

    def test_routing_thresholds_escalation_and_fallback(self):
        # Small token estimate -> should fallback to cheaper model (gpt-4o-mini or claude-haiku)
        model = self.router.route(["code"], token_estimate=1000, threshold=10000)
        self.assertIn("mini", model["id"].lower()) # gpt-4o-mini is cheap

        # Large token estimate -> should escalate to high-tier model
        model_esc = self.router.route(["code"], token_estimate=50000, threshold=10000)
        self.assertNotIn("mini", model_esc["id"].lower()) # Should be gpt-4o or sonnet

    def test_fallback_on_failure(self):
        failed_model = "gpt-4o"
        fallback = self.router.get_fallback(failed_model, ["code"], 1000)
        self.assertIsNotNone(fallback)
        self.assertNotEqual(fallback["id"], failed_model)

    def test_token_counter_and_cost_calculation(self):
        text = "A" * 400
        tokens = TokenCounter.estimate_tokens(text)
        self.assertEqual(tokens, 100)

        model_config = self.registry.get_model_by_id("gpt-4o-mini")
        cost = CostCalculator.calculate_cost(model_config, 1000, 1000)
        # 1000 tokens = 1k. Input cost 0.00015, Output 0.0006. Total = 0.00075
        self.assertAlmostEqual(cost, 0.00075)

    def test_persistent_model_stats_and_version_separation(self):
        model_config = self.registry.get_model_by_id("gpt-4o")
        cost = CostCalculator.calculate_cost(model_config, 1000, 1000)
        
        self.stats.record_call("gpt-4o", "v1", 1000, 1000, cost)
        self.stats.record_call("gpt-4o", "v2", 2000, 2000, cost * 2)
        
        # Check version separation
        v1_stats = self.stats.get_stats("gpt-4o", "v1")
        v2_stats = self.stats.get_stats("gpt-4o", "v2")
        self.assertEqual(v1_stats["total_calls"], 1)
        self.assertEqual(v2_stats["total_calls"], 1)
        self.assertEqual(v1_stats["total_input_tokens"], 1000)
        self.assertEqual(v2_stats["total_input_tokens"], 2000)
        
        # Check persistence
        new_stats_instance = ModelStats(self.stats_path)
        self.assertEqual(new_stats_instance.get_stats("gpt-4o", "v1")["total_calls"], 1)
        
        # Check aggregation
        agg_stats = self.stats.get_stats("gpt-4o")
        self.assertEqual(agg_stats["total_calls"], 2)

    def test_provider_adapter(self):
        model_config = self.registry.get_model_by_id("gpt-4o-mini")
        adapter = ProviderAdapter(model_config)
        response = adapter.call("Hello world", 100)
        self.assertIn("Response from gpt-4o-mini", response["content"])
