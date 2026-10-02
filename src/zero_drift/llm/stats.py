"""Model Stats, Token Counter, and Cost Calculation."""
import json
import os
from typing import Dict

class TokenCounter:
    @staticmethod
    def estimate_tokens(text: str) -> int:
        # Simple dummy estimation: 1 token per 4 chars
        return len(text) // 4

class CostCalculator:
    @staticmethod
    def calculate_cost(model_config: Dict, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1000.0) * model_config["input_cost_per_1k"]
        output_cost = (output_tokens / 1000.0) * model_config["output_cost_per_1k"]
        return round(input_cost + output_cost, 6)

class ModelStats:
    def __init__(self, storage_path: str = "model_stats.json"):
        self.storage_path = storage_path
        self.stats: Dict[str, Dict] = self._load()

    def _load(self) -> Dict[str, Dict]:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def record_call(self, model_id: str, version: str, input_tokens: int, output_tokens: int, cost: float):
        key = f"{model_id}:{version}" # Version separation
        if key not in self.stats:
            self.stats[key] = {
                "model_id": model_id,
                "version": version,
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0
            }
        
        entry = self.stats[key]
        entry["total_calls"] += 1
        entry["total_input_tokens"] += input_tokens
        entry["total_output_tokens"] += output_tokens
        entry["total_cost"] += cost
        self._save()

    def get_stats(self, model_id: str, version: str = None) -> Dict:
        if version:
            return self.stats.get(f"{model_id}:{version}", {})
        # Aggregate all versions
        agg = {"total_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0, "total_cost": 0.0}
        for key, data in self.stats.items():
            if data["model_id"] == model_id:
                agg["total_calls"] += data["total_calls"]
                agg["total_input_tokens"] += data["total_input_tokens"]
                agg["total_output_tokens"] += data["total_output_tokens"]
                agg["total_cost"] += data["total_cost"]
        return agg
