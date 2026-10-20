"""Git commit-msg hook installation and management."""

import os
import stat
from pathlib import Path
from typing import Dict, Optional, Tuple
from .git_utils import get_repo_root

HOOK_SIGNATURE = "# commit-scope-lint commit-msg hook"

HOOK_TEMPLATE = f"""#!/usr/bin/env sh
{HOOK_SIGNATURE}
# Automatically validates commit messages against Conventional Commits & Scope rules.

if command -v commit-scope-lint >/dev/null 2>&1; then
    commit-scope-lint --file "$1"
elif command -v python3 >/dev/null 2>&1; then
    python3 -m commit_scope_lint --file "$1"
elif command -v python >/dev/null 2>&1; then
    python -m commit_scope_lint --file "$1"
else
    echo "commit-scope-lint hook: Python / commit-scope-lint not found in PATH. Skipping check."
    exit 0
fi
"""


def get_hooks_dir(repo_root: Optional[Path] = None) -> Optional[Path]:
    """Retrieve git hooks directory."""
    root = repo_root or get_repo_root()
    if not root:
        return None
    git_dir = root / ".git"
    if not git_dir.exists():
        return None
    if git_dir.is_file():
        # Submodule or git worktree
        try:
            content = git_dir.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                git_dir = (root / content.split(":", 1)[1].strip()).resolve()
        except Exception:
            pass
    hooks_dir = git_dir / "hooks"
    return hooks_dir


def install_hook(repo_root: Optional[Path] = None, force: bool = False) -> Tuple[bool, str]:
    """Install commit-msg hook into current git repository."""
    hooks_dir = get_hooks_dir(repo_root)
    if not hooks_dir:
        return False, "Not inside a git repository (.git folder not found)."

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "commit-msg"

    if hook_file.exists() and not force:
        existing_content = hook_file.read_text(encoding="utf-8", errors="replace")
        if HOOK_SIGNATURE in existing_content:
            return True, "commit-msg hook is already installed and up to date."
        return False, f"Existing commit-msg hook found at {hook_file}. Use --force to overwrite."

    hook_file.write_text(HOOK_TEMPLATE, encoding="utf-8")

    # Set executable permissions (0755)
    try:
        current_stat = hook_file.stat().st_mode
        hook_file.chmod(current_stat | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass

    return True, f"Successfully installed commit-msg hook to {hook_file}"


def uninstall_hook(repo_root: Optional[Path] = None) -> Tuple[bool, str]:
    """Uninstall commit-msg hook from current git repository."""
    hooks_dir = get_hooks_dir(repo_root)
    if not hooks_dir:
        return False, "Not inside a git repository."

    hook_file = hooks_dir / "commit-msg"
    if not hook_file.exists():
        return False, "No commit-msg hook found."

    content = hook_file.read_text(encoding="utf-8", errors="replace")
    if HOOK_SIGNATURE not in content:
        return False, f"Hook at {hook_file} was not installed by commit-scope-lint. Not removing."

    hook_file.unlink()
    return True, f"Successfully removed commit-msg hook from {hook_file}"


def hook_status(repo_root: Optional[Path] = None) -> Dict[str, object]:
    """Check status of commit-msg hook."""
    hooks_dir = get_hooks_dir(repo_root)
    if not hooks_dir:
        return {"installed": False, "reason": "Not in a git repository", "path": None}

    hook_file = hooks_dir / "commit-msg"
    if not hook_file.exists():
        return {"installed": False, "reason": "commit-msg file does not exist", "path": str(hook_file)}

    content = hook_file.read_text(encoding="utf-8", errors="replace")
    is_our_hook = HOOK_SIGNATURE in content

    return {
        "installed": True,
        "is_managed_by_commit_scope_lint": is_our_hook,
        "path": str(hook_file),
    }
