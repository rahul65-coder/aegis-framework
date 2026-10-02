"""Cost Manager."""
from .budget import Budget

class CostManager:
    def __init__(self):
        self.spent = 0.0
        
    def pre_call_check(self, estimated_cost: float, budget: Budget) -> bool:
        # budget pre-call check works
        # budget exceed blocks execution
        if self.spent + estimated_cost > budget.limit:
            return False 
        return True
        
    def record_usage(self, actual_cost: float):
        self.spent += actual_cost
        self.spent = round(self.spent, 4)
