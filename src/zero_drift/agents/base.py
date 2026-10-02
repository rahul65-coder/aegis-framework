"""Base Agent."""
from zero_drift.llm.router import ModelRouter
from zero_drift.execution.executor import ToolExecutor
from zero_drift.llm.stats import ModelStats, CostCalculator, TokenCounter

class BaseAgent:
    def __init__(self, agent_id: str, role: str, router: ModelRouter, executor: ToolExecutor, stats: ModelStats):
        self.agent_id = agent_id
        self.role = role
        self.router = router
        self.executor = executor
        self.stats = stats

    def think(self, prompt: str, context: dict) -> str:
        """Agent thinks, routes to LLM, and records stats/cost."""
        tokens = TokenCounter.estimate_tokens(prompt)
        # Hard capability filter for code generation
        model = self.router.route(["code"], tokens)
        
        input_tokens = tokens
        output_tokens = 50 # Dummy output tokens
        cost = CostCalculator.calculate_cost(model, input_tokens, output_tokens)
        
        # Record persistent stats
        self.stats.record_call(model["id"], "v1", input_tokens, output_tokens, cost)
        return f"Thought from {self.role} agent {self.agent_id} using {model['id']}: Task planned."
