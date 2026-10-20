"""Tests for git hook management."""

from pathlib import Path
from commit_scope_lint.hook import (
    HOOK_SIGNATURE,
    get_hooks_dir,
    hook_status,
    install_hook,
    uninstall_hook,
)


def test_hook_lifecycle(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    # Initial status - not installed
    status = hook_status(repo_root=tmp_path)
    assert not status["installed"]

    # Install hook
    success, msg = install_hook(repo_root=tmp_path)
    assert success
    hook_file = git_dir / "hooks" / "commit-msg"
    assert hook_file.is_file()
    assert HOOK_SIGNATURE in hook_file.read_text(encoding="utf-8")

    # Status check
    status = hook_status(repo_root=tmp_path)
    assert status["installed"]
    assert status["is_managed_by_commit_scope_lint"]

    # Re-install without force is idempotent
    success, msg = install_hook(repo_root=tmp_path, force=False)
    assert success
    assert "already installed" in msg

    # Uninstall hook
    success, msg = uninstall_hook(repo_root=tmp_path)
    assert success
    assert not hook_file.exists()


def test_hook_foreign_file_conflict(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir()
    hook_file = hooks_dir / "commit-msg"
    hook_file.write_text("# custom legacy hook\necho 'hello'", encoding="utf-8")

    # Without force: fails
    success, msg = install_hook(repo_root=tmp_path, force=False)
    assert not success
    assert "Existing commit-msg hook found" in msg

    # Status shows not managed
    status = hook_status(repo_root=tmp_path)
    assert status["installed"]
    assert not status["is_managed_by_commit_scope_lint"]

    # Uninstall fails because not managed
    uninst_ok, uninst_msg = uninstall_hook(repo_root=tmp_path)
    assert not uninst_ok
    assert "was not installed by commit-scope-lint" in uninst_msg

    # With force: succeeds
    force_ok, force_msg = install_hook(repo_root=tmp_path, force=True)
    assert force_ok
    assert HOOK_SIGNATURE in hook_file.read_text(encoding="utf-8")


def test_hook_non_git_dir(tmp_path: Path):
    # Directory without .git
    success, msg = install_hook(repo_root=tmp_path)
    assert not success
    assert "Not inside a git repository" in msg

    uninst_ok, uninst_msg = uninstall_hook(repo_root=tmp_path)
    assert not uninst_ok


def test_hook_worktree_file(tmp_path: Path):
    # Mock gitdir file in a worktree
    actual_git = tmp_path / "actual_git"
    actual_git.mkdir()
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {actual_git.resolve()}", encoding="utf-8")

    hooks_dir = get_hooks_dir(repo_root=worktree)
    assert hooks_dir == actual_git / "hooks"
