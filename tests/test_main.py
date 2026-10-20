"""Tests for python -m commit_scope_lint execution."""

import subprocess
import sys


def test_module_execution():
    proc = subprocess.run(
        [sys.executable, "-m", "commit_scope_lint", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "commit-scope-lint 1.0.0" in proc.stdout or "commit-scope-lint 1.0.0" in proc.stderr
