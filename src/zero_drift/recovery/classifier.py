"""Error Classifier."""

class ErrorClassifier:
    def classify(self, error_msg: str) -> str:
        error_msg = error_msg.lower()
        if "timeout" in error_msg or "network" in error_msg or "api" in error_msg:
            return "TRANSIENT"
        if "permission" in error_msg or "unauthorized" in error_msg or "auth" in error_msg:
            return "PERMANENT"
        if "crash" in error_msg or "kill" in error_msg or "segfault" in error_msg or "segmentation" in error_msg or "core dumped" in error_msg or "exit" in error_msg:
            return "CRASH"
        return "UNKNOWN"
