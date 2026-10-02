"""Tool Executor - Integrates Event Log, Scope, and FileOps."""
from zero_drift.events.log import EventLog
from .scope import ScopeEnforcer
from .file_ops import hash_checked_edit, compute_hash

class ToolExecutor:
    def __init__(self, event_log: EventLog, scope_enforcer: ScopeEnforcer):
        self.event_log = event_log
        self.scope = scope_enforcer

    def execute_file_edit(self, agent_id: str, file_path: str, expected_hash: str, new_content: str, idempotency_key: str):
        self.scope.validate_path(file_path)
        intent_id = self.event_log.log_intent(idempotency_key, {"action": "file_edit", "path": file_path})
        try:
            hash_checked_edit(file_path, expected_hash, new_content)
            self.event_log.log_result(intent_id, {"status": "success", "new_hash": compute_hash(file_path)})
        except Exception as e:
            self.event_log.log_failure(intent_id, {"status": "failure", "error": str(e)})
            raise
