"""Tests for git repository utilities."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from commit_scope_lint.git_utils import (
    get_commit_message_from_file,
    get_commit_range,
    get_last_n_commits,
    get_repo_root,
    is_git_repo,
    parse_git_log_output,
)


def test_parse_git_log_output():
    # Delimited by %x1e (record) and %x1f (unit)
    raw = (
        "1111111\x1fAlice\x1ffeat(auth): add login\x1e"
        "2222222\x1fBob\x1ffix(db): handle disconnect\n\nFixes #12\x1e"
    )
    records = parse_git_log_output(raw)
    assert len(records) == 2
    assert records[0] == ("1111111", "Alice", "feat(auth): add login")
    assert records[1][0] == "2222222"
    assert records[1][1] == "Bob"
    assert "handle disconnect" in records[1][2]


def test_get_commit_message_from_file(tmp_path: Path):
    f = tmp_path / "COMMIT_EDITMSG"
    f.write_text("feat(core): initial scaffold\n\n# comment\n", encoding="utf-8")
    msg = get_commit_message_from_file(f)
    assert "feat(core): initial scaffold" in msg

    with pytest.raises(FileNotFoundError):
        get_commit_message_from_file(tmp_path / "non_existent")


def test_get_repo_root_and_is_git_repo():
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "/path/to/repo\n"
        mock_run.return_value = mock_proc

        root = get_repo_root()
        assert root == Path("/path/to/repo")
        assert is_git_repo()

    with patch("subprocess.run", side_effect=subprocess.SubprocessError):
        assert get_repo_root() is None
        assert not is_git_repo()


def test_get_commit_range_mock():
    mock_out = "hash1\x1fAuthor1\x1ffeat: test commit\x1e"
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = mock_out
        mock_run.return_value = mock_proc

        commits = get_commit_range("main", "HEAD")
        assert len(commits) == 1
        assert commits[0][0] == "hash1"


def test_get_commit_range_failure():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["git"], stderr="fatal: bad revision")):
        with pytest.raises(RuntimeError) as exc_info:
            get_commit_range("bad_rev")
        assert "fatal: bad revision" in str(exc_info.value)


def test_get_last_n_commits_mock():
    assert get_last_n_commits(0) == []
    mock_out = "hashA\x1fAuthorA\x1ffix(ui): fix button\x1e"
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = mock_out
        mock_run.return_value = mock_proc

        commits = get_last_n_commits(1)
        assert len(commits) == 1
        assert commits[0][0] == "hashA"
