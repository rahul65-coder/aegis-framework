"""File Operations, Leases, and Hash-Checked Edits."""
import os
import hashlib

class FileLeaseManager:
    def __init__(self):
        self.leases = {}

    def acquire_lease(self, file_path: str, agent_id: str):
        if file_path in self.leases and self.leases[file_path] != agent_id:
            raise ValueError(f"File lease collision: {file_path} is locked by {self.leases[file_path]}")
        self.leases[file_path] = agent_id

    def release_lease(self, file_path: str, agent_id: str):
        if file_path in self.leases and self.leases[file_path] == agent_id:
            del self.leases[file_path]

def compute_hash(file_path: str) -> str:
    if not os.path.exists(file_path): return ""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def hash_checked_edit(file_path: str, expected_hash: str, new_content: str):
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    current_hash = compute_hash(file_path)
    if current_hash != expected_hash:
        raise ValueError(f"Hash mismatch for {file_path}. Expected {expected_hash}, got {current_hash}")
    with open(file_path, 'w') as f:
        f.write(new_content)
