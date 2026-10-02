"""Task Engine."""
import hashlib
from collections import namedtuple

ObjectiveLock = namedtuple('ObjectiveLock', ['objective', 'locked', 'hash'])

class TaskEngine:
    def decompose_prompt(self, prompt: str) -> list:
        # Simple dummy decomposition
        return [f"task_1_{prompt[:10]}", f"task_2_{prompt[:10]}"]

    def lock_objective(self, objective: str) -> ObjectiveLock:
        # Immutable lock
        obj_hash = hashlib.sha256(objective.encode()).hexdigest()
        return ObjectiveLock(objective=objective, locked=True, hash=obj_hash)
