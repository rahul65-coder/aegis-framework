"""Mode Selector."""

class ModeSelector:
    def suggest_mode(self, estimate: dict) -> str:
        if estimate.get("cost", 0) > 0.05 or estimate.get("tokens", 0) > 5000:
            return "PROMAX"
        return "STANDARD"
