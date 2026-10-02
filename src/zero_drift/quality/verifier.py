"""Verifier."""
from .claims import Claim

class Verifier:
    def verify(self, claim: Claim) -> str:
        status = claim.validate()
        # failed evidence != VERIFIED
        if status == "FAILED":
            return "FAILED"
        if status == "UNKNOWN":
            return "UNKNOWN"
        return "VERIFIED"

    def protect_verified_node(self, node_status: str, new_evidence: dict) -> bool:
        # verified nodes are protected against downgrade without explicit override
        if node_status == "VERIFIED" and not new_evidence.get("force_override"):
            return False
        return True
