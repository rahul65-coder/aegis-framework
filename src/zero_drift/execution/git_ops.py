"""Git Operations."""
import subprocess

class GitOps:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _run_git(self, args: list):
        return subprocess.run(["git"] + args, cwd=self.repo_path, capture_output=True, text=True)

    def create_worktree(self, worktree_path: str, branch_name: str):
        res = self._run_git(["worktree", "add", "-b", branch_name, worktree_path])
        if res.returncode != 0:
            raise ValueError(f"Failed to create worktree: {res.stderr}")
        return worktree_path

    def remove_worktree(self, worktree_path: str):
        self._run_git(["worktree", "remove", worktree_path, "--force"])

    def commit_changes(self, message: str):
        self._run_git(["add", "."])
        res = self._run_git(["commit", "-m", message])
        if res.returncode != 0 and "nothing to commit" not in res.stdout:
            raise ValueError(f"Git commit failed: {res.stderr}")
        return True

    def rollback(self, commit_hash: str):
        res = self._run_git(["reset", "--hard", commit_hash])
        if res.returncode != 0:
            raise ValueError(f"Rollback failed: {res.stderr}")
