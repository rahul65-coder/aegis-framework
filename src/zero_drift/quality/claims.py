"""Claims & Evidence Handling."""

class Claim:
    def __init__(self, statement: str, evidence: dict = None):
        self.statement = statement
        self.evidence = evidence
        self.status = "UNKNOWN"

    def validate(self):
        if self.evidence is None:
            self.status = "UNKNOWN"
        elif self.evidence.get("passed"):
            self.status = "VERIFIED"
        else:
            self.status = "FAILED"
        return self.status

def is_agent_self_claim_sufficient(claim: Claim) -> bool:
    # agent self-claim != evidence
    if claim.evidence is None or claim.evidence.get("source") == "agent_self":
        return False
    return True
