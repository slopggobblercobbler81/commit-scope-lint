"""Git repository utilities and commit log extraction."""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union


def get_repo_root() -> Optional[Path]:
    """Retrieve the root directory of the current git repository."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(proc.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def is_git_repo() -> bool:
    """Return True if current working directory is inside a git repository."""
    return get_repo_root() is not None


def get_commit_message_from_file(file_path: Union[str, Path]) -> str:
    """Read commit message from file (e.g. .git/COMMIT_EDITMSG)."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Commit message file not found: {file_path}")
    return p.read_text(encoding="utf-8", errors="replace")


def parse_git_log_output(output: str) -> List[Tuple[str, str, str]]:
    """Parse delimiter-separated git log output into (hash, author, message) tuples."""
    commits: List[Tuple[str, str, str]] = []
    # %x1e is record separator, %x1f is unit separator
    records = output.strip().split("\x1e")
    for record in records:
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) >= 3:
            commit_hash = parts[0].strip()
            author = parts[1].strip()
            message = parts[2].strip()
            commits.append((commit_hash, author, message))
        elif len(parts) == 1 and parts[0]:
            commits.append(("", "", parts[0].strip()))
    return commits


def get_commit_range(from_rev: str, to_rev: str = "HEAD") -> List[Tuple[str, str, str]]:
    """Get commit messages in the revision range from_rev..to_rev."""
    rev_spec = f"{from_rev}..{to_rev}"
    cmd = [
        "git",
        "log",
        f"--format=%H%x1f%an%x1f%B%x1e",
        rev_spec,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return parse_git_log_output(proc.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e.stderr.strip() or e.stdout.strip()}")


def get_last_n_commits(n: int = 1) -> List[Tuple[str, str, str]]:
    """Get the last n commits from current branch."""
    if n <= 0:
        return []
    cmd = [
        "git",
        "log",
        f"-n",
        str(n),
        f"--format=%H%x1f%an%x1f%B%x1e",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return parse_git_log_output(proc.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e.stderr.strip() or e.stdout.strip()}")


def read_stdin() -> str:
    """Read all text from standard input."""
    return sys.stdin.read()
