"""Model Registry & Provider Loading."""
import yaml
import os
from typing import List, Dict, Any

class ModelRegistry:
    def __init__(self, config_path: str = "src/zero_drift/llm/providers.yaml"):
        self.models: List[Dict[str, Any]] = []
        self.load_providers(config_path)

    def load_providers(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Providers config not found at {config_path}")
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        for provider in data.get("providers", []):
            provider_name = provider["name"]
            for model in provider.get("models", []):
                self.models.append({
                    "provider": provider_name,
                    "id": model["id"],
                    "context_window": model["context_window"],
                    "capabilities": set(model.get("capabilities", [])),
                    "input_cost_per_1k": model.get("input_cost_per_1k", 0.0),
                    "output_cost_per_1k": model.get("output_cost_per_1k", 0.0)
                })

    def get_models(self, required_capabilities: List[str] = None, min_context_window: int = 0) -> List[Dict[str, Any]]:
        filtered = []
        for model in self.models:
            if model["context_window"] < min_context_window:
                continue
            if required_capabilities:
                if not set(required_capabilities).issubset(model["capabilities"]):
                    continue
            filtered.append(model)
        return filtered

    def get_model_by_id(self, model_id: str) -> Dict[str, Any]:
        for model in self.models:
            if model["id"] == model_id:
                return model
        raise ValueError(f"Model {model_id} not found in registry")
