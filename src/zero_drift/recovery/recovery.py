"""Error Recovery Engine."""
from zero_drift.events.log import EventLog
from zero_drift.state.manager import StateManager

class RecoveryEngine:
    def __init__(self, event_log: EventLog, state_mgr: StateManager):
        self.event_log = event_log
        self.state_mgr = state_mgr

    def recover_incomplete_actions(self) -> dict:
        # Inspect checkpoint and event log
        partial = self.state_mgr.detect_partial_actions()
        incomplete_intents = self.event_log.get_incomplete_events()
        
        recovered_actions = []
        for intent in incomplete_intents:
            # System does NOT blindly repeat already completed work
            recovered_actions.append(intent["idempotency_key"])
            
        return {
            "partial_checkpoint": partial,
            "actions_to_recover": recovered_actions
        }
