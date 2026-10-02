"""Approval System."""

class ApprovalSystem:
    def request_approval(self, plan: dict, estimate: dict) -> bool:
        # User approval gate works: blocks by default until explicitly granted
        return False 
        
    def grant_approval(self, user_decision: bool) -> bool:
        return user_decision
