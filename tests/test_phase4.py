"""Phase 4 Verification Tests."""
import os
import tempfile
import shutil
import subprocess
import unittest

from zero_drift.db.connection import get_connection
from zero_drift.db.migrations import run_migrations
from zero_drift.events.log import EventLog
from zero_drift.execution.scope import ScopeEnforcer
from zero_drift.execution.file_ops import FileLeaseManager, hash_checked_edit, compute_hash
from zero_drift.execution.shell import run_shell_command
from zero_drift.execution.git_ops import GitOps
from zero_drift.execution.executor import ToolExecutor

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_phase4.db"
        self.cleanup_db()
        self.conn = get_connection(self.db_path)
        run_migrations(self.conn)
        self.event_log = EventLog(self.conn)
        
        self.temp_dir = tempfile.mkdtemp()
        self.scope = ScopeEnforcer([self.temp_dir])
        self.executor = ToolExecutor(self.event_log, self.scope)
        self.lease_mgr = FileLeaseManager()

    def tearDown(self):
        self.conn.close()
        self.cleanup_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def cleanup_db(self):
        for ext in ["", "-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.remove(p)

    def test_scope_violation_rejected(self):
        with self.assertRaises(ValueError) as context:
            self.scope.validate_path("/etc/passwd")
        self.assertIn("Scope violation", str(context.exception))

    def test_hash_mismatch_rejected(self):
        file_path = os.path.join(self.temp_dir, "test.txt")
        with open(file_path, "w") as f: f.write("hello")
        
        with self.assertRaises(ValueError) as context:
            hash_checked_edit(file_path, "wrong_hash", "world")
        self.assertIn("Hash mismatch", str(context.exception))

    def test_file_lease_collision_rejected(self):
        self.lease_mgr.acquire_lease("file.txt", "agent_1")
        with self.assertRaises(ValueError) as context:
            self.lease_mgr.acquire_lease("file.txt", "agent_2")
        self.assertIn("File lease collision", str(context.exception))

    def test_shell_timeout_works(self):
        result = run_shell_command(["sleep", "2"], timeout=1)
        self.assertEqual(result["stderr"], "TimeoutExpired")
        self.assertEqual(result["returncode"], -1)

    def test_git_worktree_commit_and_rollback(self):
        # Init a dummy git repo in temp_dir
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.temp_dir, capture_output=True, check=True)
        
        # Create initial commit
        dummy_file = os.path.join(self.temp_dir, "dummy.txt")
        with open(dummy_file, "w") as f: f.write("initial")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.temp_dir, capture_output=True, check=True)
        
        git_ops = GitOps(self.temp_dir)
        
        # Worktree test
        wt_path = os.path.join(self.temp_dir, "wt")
        git_ops.create_worktree(wt_path, "feature-branch")
        self.assertTrue(os.path.exists(wt_path))
        git_ops.remove_worktree(wt_path)
        self.assertFalse(os.path.exists(wt_path))
        
        # Commit test
        new_file = os.path.join(self.temp_dir, "new.txt")
        with open(new_file, "w") as f: f.write("new")
        git_ops.commit_changes("added new file")
        self.assertTrue(os.path.exists(new_file))
        
        # Rollback test
        init_hash = subprocess.check_output(["git", "rev-parse", "HEAD~1"], cwd=self.temp_dir).decode().strip()
        git_ops.rollback(init_hash)
        self.assertFalse(os.path.exists(new_file))

    def test_intent_logged_before_side_effect_and_result_after(self):
        file_path = os.path.join(self.temp_dir, "edit.txt")
        with open(file_path, "w") as f: f.write("v1")
        
        expected_hash = compute_hash(file_path)
        
        self.executor.execute_file_edit(
            agent_id="agent_1",
            file_path=file_path,
            expected_hash=expected_hash,
            new_content="v2",
            idempotency_key="edit_key_1"
        )
        
        # Verify event log has INTENT and RESULT
        cursor = self.conn.execute("SELECT event_type FROM events WHERE idempotency_key = 'edit_key_1' OR event_type = 'RESULT' ORDER BY id")
        events = [row["event_type"] for row in cursor.fetchall()]
        self.assertIn("INTENT", events)
        self.assertIn("RESULT", events)
        self.assertEqual(events[0], "INTENT")
