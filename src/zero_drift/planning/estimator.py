"""Estimator."""

class Estimator:
    def estimate(self, plan: dict) -> dict:
        # Dummy estimation based on number of steps
        steps = len(plan.get("steps", []))
        return {
            "tokens": steps * 2500,
            "cost": round(steps * 0.025, 4),
            "time_seconds": steps * 30
        }
