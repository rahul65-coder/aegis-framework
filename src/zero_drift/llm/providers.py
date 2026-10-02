"""Provider Adapters."""
from typing import Dict

class ProviderAdapter:
    def __init__(self, model_config: Dict):
        self.model_config = model_config

    def call(self, prompt: str, max_tokens: int) -> Dict:
        # Dummy response for testing routing/stats
        return {
            "content": f"Response from {self.model_config['id']}",
            "input_tokens": len(prompt) // 4,
            "output_tokens": max_tokens // 2
        }
