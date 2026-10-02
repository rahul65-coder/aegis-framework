"""Resume System."""
from .recovery import RecoveryEngine

class ResumeSystem:
    def __init__(self, recovery_engine: RecoveryEngine):
        self.recovery = recovery_engine
        self.resumed_sessions = {}

    def resume_session(self, session_id: str):
        if self.resumed_sessions.get(session_id):
            # Already resumed, do not duplicate work
            return "ALREADY_RESUMED"
        
        # Inspect state, recover incomplete actions
        state = self.recovery.recover_incomplete_actions()
        self.resumed_sessions[session_id] = True
        
        return {
            "session_id": session_id,
            "status": "RESUMED",
            "recovered_actions": state["actions_to_recover"]
        }
