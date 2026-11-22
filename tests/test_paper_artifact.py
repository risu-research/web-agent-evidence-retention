"""Check that archived paper results stay aligned with the public metadata."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PaperArtifactTests(unittest.TestCase):
    def test_main_tables_and_recorded_provenance(self):
        outcome = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_paper_artifact.py")],
            cwd=ROOT, check=False, capture_output=True, text=True,
        )
        self.assertEqual(outcome.returncode, 0, outcome.stdout + outcome.stderr)
        self.assertIn("PASS: frozen 600/55 cohort", outcome.stdout)


if __name__ == "__main__":
    unittest.main()
