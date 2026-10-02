import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestPhase0Foundation(unittest.TestCase):
    def test_required_files_exist(self):
        required_files = [
            "README.md",
            "ARCHITECTURE.md",
            "docs/GLOBAL_RULES.md",
            "docs/PHASE_STATUS.md",
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            ".github/workflows/ci.yml",
            "src/zero_drift/__init__.py",
        ]

        for file_path in required_files:
            self.assertTrue(
                (ROOT / file_path).exists(),
                f"Missing required Phase 0 file: {file_path}",
            )

    def test_package_metadata_exists(self):
        init_file = ROOT / "src/zero_drift/__init__.py"
        content = init_file.read_text(encoding="utf-8")

        self.assertIn("AEGIS ZERO", content)
        self.assertIn("__version__", content)


if __name__ == "__main__":
    unittest.main()
