"""Model Router."""
from typing import List, Dict, Any, Optional
from .registry import ModelRegistry

class ModelRouter:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def route(self, required_capabilities: List[str], token_estimate: int, threshold: int = 10000) -> Dict[str, Any]:
        # Hard capability & context window filter
        candidates = self.registry.get_models(required_capabilities, token_estimate)
        if not candidates:
            raise ValueError("No models meet the hard capability and context window filters")

        # Routing threshold logic: if token_estimate > threshold, escalate to high-tier, else fallback to low-tier
        high_tier = [m for m in candidates if m["input_cost_per_1k"] >= 0.003] # Arbitrary tier definition
        low_tier = [m for m in candidates if m["input_cost_per_1k"] < 0.003]

        if token_estimate > threshold:
            # Escalation
            if high_tier:
                return high_tier[0]
            return candidates[0] # Fallback to best available if high tier empty
        else:
            # Fallback to cheaper
            if low_tier:
                return low_tier[0]
            return candidates[0]

    def get_fallback(self, failed_model_id: str, required_capabilities: List[str], token_estimate: int) -> Optional[Dict[str, Any]]:
        candidates = self.registry.get_models(required_capabilities, token_estimate)
        # Exclude the failed model
        fallbacks = [m for m in candidates if m["id"] != failed_model_id]
        if fallbacks:
            return fallbacks[0]
        return None
