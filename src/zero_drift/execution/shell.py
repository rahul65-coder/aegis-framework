"""Shell Execution & Sandbox Simulation."""
import subprocess

def run_shell_command(command: list, timeout: int = 10):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "TimeoutExpired"
        }
