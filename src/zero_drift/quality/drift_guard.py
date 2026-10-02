"""Drift Guard."""
import os

class DriftGuard:
    def __init__(self, allowed_scope: list):
        self.allowed_scope = [os.path.abspath(p) for p in allowed_scope]

    def detect_scope_drift(self, modified_files: list) -> bool:
        for f in modified_files:
            abs_f = os.path.abspath(f)
            if not any(abs_f.startswith(scope) for scope in self.allowed_scope):
                return True # Scope drift detected
        return False

    def detect_unrelated_modification(self, intended_target: str, modified_files: list) -> bool:
        # unrelated modification is detected if any file is not the target or inside target dir
        abs_target = os.path.abspath(intended_target)
        for f in modified_files:
            abs_f = os.path.abspath(f)
            if abs_f == abs_target:
                continue
            if abs_f.startswith(abs_target + os.sep):
                continue
            return True
        return False
