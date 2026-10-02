"""Planner."""

class Planner:
    def generate_plan(self, tasks: list) -> dict:
        return {"steps": tasks, "status": "planned"}

    def handle_ambiguity(self, prompt: str) -> str:
        # ambiguity causes approval/question instead of assumption
        if "?" in prompt or "ambiguous" in prompt.lower() or "maybe" in prompt.lower():
            return "APPROVAL_REQUIRED"
        return "CLEAR"
