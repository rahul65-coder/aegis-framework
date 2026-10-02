"""Scope Enforcement."""
import os

class ScopeEnforcer:
    def __init__(self, allowed_paths: list):
        self.allowed_paths = [os.path.abspath(p) for p in allowed_paths]

    def validate_path(self, path: str):
        abs_path = os.path.abspath(path)
        for allowed in self.allowed_paths:
            if abs_path.startswith(allowed):
                return True
        raise ValueError(f"Scope violation: {path} is outside allowed paths")
